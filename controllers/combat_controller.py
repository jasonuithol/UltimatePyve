import pygame
import random

from controllers.active_member_controller import ActiveMemberController
from controllers.cast_controller import CastController
from controllers.move_controller import MoveController

from controllers.ready_controller import ReadyController
from dark_libraries.dark_events import DarkEventListenerMixin, DarkEventService
from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.agents.party_member_agent import PartyMemberAgent
from models.combat_map import CombatMap
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
from models.enums.cursor_type import CursorType
from models.enums.direction_map import DIRECTION_MAP
from models.enums.hit_point_level import get_hp_level_text
from models.enums.projectile_type import ProjectileType
from models.global_location import GlobalLocation

from models.location_metadata import LocationMetadata
from models.agents.monster_agent import MonsterAgent
from models.agents.party_agent import PartyAgent
from models.u5_map import U5Map
from models.equipable_item_type import EquipableItemType # for syntax highlighting

from services.combat_map_service import CombatMapService
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.main_loop_service import MainLoopService
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService
from services.sfx_library_service import SfxLibraryService
from services.view_port_service import ViewPortService


def wrap_combat_map_in_u5map(combat_map: CombatMap) -> U5Map:
    return U5Map(
        {0:combat_map},
        LocationMetadata(
            location_index = COMBAT_MAP_LOCATION_INDEX, # index of the location for things like WorldLootLoader, and GlobalLocation references.
            name = "COMBAT",                            # name of the location

            name_index       = None, # which name the location takes.
            files_index      = None, # which file the location is in
            group_index      = None, # order of appearance of the town in the file. Use for indexing into DATA.OVL properties.
            map_index_offset = None, # how many levels to skip to start reading the first level of the location.

            num_levels    = 0,       # how many levels the location contains
            default_level = 0,       # which level the player spawns in when entering the location.
            has_basement  = False,
            trigger_index = None,    # the index the entry triggers for this location are at.
            sound_track   = None     # an absolute path to the soundtrack                
        )
    )    

IN_COMBAT = True
COMBAT_OVER = False

class CombatController(DarkEventListenerMixin, LoggerMixin):

    # Injectable
    party_agent: PartyAgent
    npc_service: NpcService
    combat_map_service: CombatMapService
    global_registry: GlobalRegistry
    map_cache_service: MapCacheService
    console_service: ConsoleService
    
    main_loop_service: MainLoopService
    dark_event_service: DarkEventService
    display_service: DisplayService
    move_controller: MoveController
    active_member_controller: ActiveMemberController
    ready_controller: ReadyController
    cast_controller: CastController
    sfx_library_service: SfxLibraryService
    view_port_service: ViewPortService

    _last_attacked_monster = dict[str, MonsterAgent]()

    def _enter_combat_arena(self, enemy_party: MonsterAgent) -> CombatMap:
        party_transport_mode_index, _ = self.party_agent.get_transport_state()

        combat_map = self.combat_map_service.get_combat_map(
            self.party_agent.get_current_location(),
            party_transport_mode_index,
            enemy_party
        )

        combat_map_wrapper = wrap_combat_map_in_u5map(combat_map)

        # We have dynamically loaded a map with no location index.
        # Register and cache it under location_index -666, level_index = 0, overwriting any previously registered/cached combat map.
        self.global_registry.maps.register(combat_map_wrapper.location_index, combat_map_wrapper)
        self.map_cache_service.cache_u5map(combat_map_wrapper)

        self.view_port_service.set_combat_mode()

        self.party_agent.push_location(GlobalLocation(COMBAT_MAP_LOCATION_INDEX, 0, Coord(5, 9)))

        # NPC freezing happens here.
        self.dark_event_service.pass_time(self.party_agent.get_current_location())
        return combat_map

    def _spawn_monsters(self, combat_map: CombatMap, enemy_party: MonsterAgent):
        if enemy_party._npc_metadata.max_party_size <= 1:
            monster_party_size = 1
        else:
            monster_party_size = random.randint(1, enemy_party._npc_metadata.max_party_size)

        for monster_spawn_slot_index in range(monster_party_size):
            spawn_coord: Coord = combat_map._monster_spawn_coords[monster_spawn_slot_index]
            clone: MonsterAgent = enemy_party.spawn_clone_at(spawn_coord)
            clone.enter_combat(spawn_coord)
            self.npc_service.add_npc(clone)

    def _spawn_party_members(self, combat_map: CombatMap):
        for party_member_index, party_member in enumerate(self.party_agent.get_party_members()):
            spawn_coord: Coord = combat_map._party_spawn_coords[0][party_member_index]
            party_member.enter_combat(spawn_coord)
            self.npc_service.add_npc(party_member)

    def _dispatch_player_event(self, combat_map: CombatMap, party_member: PartyMemberAgent, event: pygame.event.Event) -> bool:

        current_coord = party_member.coord

        if self._has_quit:
            return COMBAT_OVER

        # Wait dispatch handler
        if event.key == pygame.K_SPACE:
            self.log("DEBUG: Wait command received")
            party_member.spend_action_quanta()
            return IN_COMBAT

        # hand event to sub-controllers
        self.active_member_controller.handle_event(event)
        self.ready_controller.handle_event(event)
        self.cast_controller.handle_event(event, spell_caster = party_member, combat_map = combat_map)

        # Attack dispatch handler
        if event.key == pygame.K_a:

            #
            # BUG: This causes pressing A to attack with all weapons one after the other without further prompting.
            #
            for weapon in party_member.get_weapons():

                self.console_service.print_ascii(weapon.name + " - ", include_carriage_return = False)

                #
                # AIMING
                #
                target_enemy = None# self._last_attacked_monster.get(party_member.name, None)
                if target_enemy is None:
                    starting_coord = party_member.coord
                else:
                    starting_coord = target_enemy.coord

                target_coord = self.main_loop_service.obtain_cursor_position(
                    starting_coord = starting_coord,
                    boundary_rect  = combat_map.get_size().to_rect(Coord(0,0)),
                    range_         = max(weapon.range_, 1)
                )
                if target_coord is None or target_coord == party_member.coord:
                    continue

                #
                # FIRING / SWINGING
                #
                self.sfx_library_service.emit_projectile(
                    projectile_type    = ProjectileType.ThrowingAxe,
                    start_world_coord  = party_member.coord,
                    finish_world_coord = target_coord
                )

                target_enemy: MonsterAgent = self.npc_service.get_npc_at(target_coord)

                # Cursor positioning over.  Do we have an enemy ?

                if target_enemy is None:
                    self.log(f"DEBUG: No enemy found at {target_coord}")
                else:
                    self._last_attacked_monster[party_member.name] = target_enemy

                    self.console_service.print_ascii(f"Attacking {target_enemy.name} !")
                    did_attack_hit = party_member.attack(target_enemy, weapon)
                    if did_attack_hit:
                        #
                        # INFLICT DAMAGE
                        #
                        enemy_health_condition = get_hp_level_text(target_enemy.hitpoints / target_enemy.maximum_hitpoints) 

                        self.console_service.print_ascii(target_enemy.name + " " + enemy_health_condition + f"!")

                        self.sfx_library_service.damage(target_coord)

                        if target_enemy.hitpoints <= 0:
                            self.npc_service.remove_npc(target_enemy)
                    else:
                        #
                        # MISSED 
                        #
                        self.console_service.print_ascii("Missed !")
                party_member.spend_action_quanta()
            return IN_COMBAT

        # Move dispatch handler
        move_offset = DIRECTION_MAP.get(event.key, None)
        if not move_offset is None:
            move_outcome = self.move_controller.move(
                GlobalLocation(COMBAT_MAP_LOCATION_INDEX, 0, current_coord), 
                move_offset, 
                'walk'
            )

            party_member.spend_action_quanta()

            if move_outcome.exit_map:
                party_member.exit_combat()
                self.npc_service.remove_npc(party_member)
                self.log(f"Party member {party_member.name} exited !")
                if not any(self.party_agent.get_party_members_in_combat()):
                    # Exit combat
                    return COMBAT_OVER
                else:
                    return IN_COMBAT

            elif move_outcome.success:
                self.log(f"DEBUG: Combat move received: {move_offset}")
                party_member.coord = party_member.coord + move_offset
            else:
                self.log(f"DEBUG: Combat move command failed: {move_outcome}")
            return IN_COMBAT

        # No more dispatchers.            
        self.log(f"DEBUG: Received non-processable event: {event.key}")
        return IN_COMBAT

    def _exit_combat_arena(self, enemy_party: MonsterAgent):

        self.log(f"Exiting combat with {enemy_party.name}")

        self.view_port_service.remove_cursor(CursorType.OUTLINE)

        for party_member in self.party_agent.get_party_members_in_combat():
            party_member.exit_combat()

        self.party_agent.pop_location()

        self.view_port_service.set_party_mode()        

        # NPC unfreezing happens here.
        self.dark_event_service.pass_time(self.party_agent.get_current_location())

        self.npc_service.set_attacking_npc(None)
        self.npc_service.remove_npc(enemy_party)

    #
    # PUBLIC METHODS
    #     
    def enter_combat(self, enemy_party: MonsterAgent):

        self.log(f"Entered combat with {enemy_party.name}")
        self.console_service.print_ascii(f"{enemy_party.name}s !")

        combat_map = self._enter_combat_arena(enemy_party)

        # Monster member spawning
        self._spawn_monsters(combat_map, enemy_party)

        # Party member spawning
        self._spawn_party_members(combat_map)

        in_combat = IN_COMBAT

        while in_combat and (not self._has_quit):

            next_turn_npc = self.npc_service.get_next_moving_npc()
            if isinstance(next_turn_npc, PartyMemberAgent):
                #
                # -- PLAYER MEMBER TURN --
                #
                party_member: PartyMemberAgent = next_turn_npc

                if not party_member.is_in_combat():
                    continue

                self.console_service.print_ascii(f"{party_member.name}, armed with {party_member.armed_with_description()}")

                cursor_sprite = self.global_registry.cursors.get(CursorType.OUTLINE.value)
                self.view_port_service.set_cursor(CursorType.OUTLINE, party_member.coord, cursor_sprite)
                #
                # -- R E N D E R --
                #
                event = self.main_loop_service.get_next_event()

                in_combat = self._dispatch_player_event(combat_map, party_member, event)

            else:
    
                # All members moved - give the monsters a turn
                if any(self.party_agent.get_party_members_in_combat()):

                    #
                    # TODO: More sophisticated AI can come later.
                    #
                    monster_target_coord = self.party_agent.get_party_members_in_combat()[0].coord

                    self.dark_event_service.pass_time(GlobalLocation(COMBAT_MAP_LOCATION_INDEX, 0, monster_target_coord))

        self._exit_combat_arena(enemy_party)

    