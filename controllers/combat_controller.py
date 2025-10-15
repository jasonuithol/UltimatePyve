import pygame
import random

from controllers.move_controller import MoveController

from dark_libraries.dark_events import DarkEventService
from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.agents.party_member_agent import PartyMemberAgent
from models.enums.direction_map import DIRECTION_MAP
from models.global_location import GlobalLocation

from models.location_metadata import LocationMetadata
from models.agents.monster_agent import MonsterAgent
from models.agents.party_agent import PartyAgent
from models.u5_map import U5Map

from services.combat_map_service import CombatMapService
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.main_loop_service import MainLoopService
from services.map_cache.map_cache_service import MapCacheService
from services.npc_service import NpcService

COMBAT_MAP_LOCATION_INDEX = -666

class CombatController(LoggerMixin):

    # Injectable
    party_agent: PartyAgent
    npc_service: NpcService
    combat_map_service: CombatMapService
    global_registry: GlobalRegistry
    map_cache_service: MapCacheService
    console_service: ConsoleService
    
    # Idea #1
    main_loop_service: MainLoopService
    dark_event_service: DarkEventService
    display_service: DisplayService
    move_controller: MoveController

    def enter_combat(self, enemy_npc: MonsterAgent):

        self.log(f"Entered combat with {enemy_npc.name}")

        self.console_service.print_ascii(f"{enemy_npc.name}s !")

        party_transport_mode_index, _ = self.party_agent.get_transport_state()

        combat_map = self.combat_map_service.get_combat_map(
            self.party_agent.get_current_location(),
            party_transport_mode_index,
            enemy_npc
        )

        combat_map_wrapper = U5Map(
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
                trigger_index = None,    # the index the entry triggers for this location are at.
                sound_track   = None     # an absolute path to the soundtrack                
            )
        )

        # TODO: Remove this
        self.global_registry.maps.register(combat_map_wrapper.location_index, combat_map_wrapper)
        self.map_cache_service.cache_u5map(combat_map_wrapper)

        self.party_agent.push_location(GlobalLocation(COMBAT_MAP_LOCATION_INDEX, 0, Coord(5, 9)))

        # NPC freezing happens here.
        self.dark_event_service.pass_time(self.party_agent.get_current_location())

        # Monster member spawning
        if enemy_npc._npc_metadata.max_party_size <= 1:
            monster_party_size = 1
        else:
            monster_party_size = random.randint(1, enemy_npc._npc_metadata.max_party_size)

        for monster_spawn_slot_index in range(monster_party_size):
            spawn_coord: Coord = combat_map._monster_spawn_coords[monster_spawn_slot_index]
            clone: MonsterAgent = enemy_npc.spawn_clone_at(spawn_coord)
            clone.enter_combat(spawn_coord)
            self.npc_service.add_npc(clone)

        # Party member spawning
        print(combat_map._party_spawn_coords)
        for party_member_index, party_member in enumerate(self.party_agent.get_party_members()):
            spawn_coord: Coord = combat_map._party_spawn_coords[0][party_member_index]
            party_member.enter_combat(spawn_coord)
            self.npc_service.add_npc(party_member)

        in_combat = True

        while in_combat:


            next_turn_npc = self.npc_service.get_next_moving_npc()

            if isinstance(next_turn_npc, PartyMemberAgent):
                party_member: PartyMemberAgent = next_turn_npc

                if not party_member.is_in_combat():
                    continue

                current_coord = party_member.coord

                self.log(f"{party_member.name}'s turn")

                #
                # -- R E N D E R --
                #
                event = self.main_loop_service.get_next_event()

                if event.type == pygame.QUIT:
                    self.console_service.print_ascii("Cannot quit during combat !")
                    continue

                if event.key == pygame.K_SPACE:
                    self.log("DEBUG: Wait command received")
                    party_member.spend_action_quanta()
                    continue

                move_offset = DIRECTION_MAP.get(event.key, None)
                if not move_offset is None:
                    move_outcome = self.move_controller.move(
                        GlobalLocation(-666, 0, current_coord), 
                        move_offset, 
                        'walk'
                    )

                    party_member.spend_action_quanta()

                    if move_outcome.exit_map:
                        party_member.exit_combat()
                        self.npc_service.remove_npc(party_member)
                        self.log(f"Party member {party_member.name} exited !")
                        if not any(self.party_agent.get_party_members_in_combat()):
                            in_combat = False
                            break
                        else:
                            continue

                    elif move_outcome.success:
                        self.log(f"DEBUG: Combat move received: {move_offset}")
                        party_member.coord = party_member.coord + move_offset
                    else:
                        self.log(f"DEBUG: Combat move command failed: {move_outcome}")
                else:
                    self.log(f"DEBUG: Received non-processable event: {event.key}")

            else:
    
                # All members moved - give the monsters a turn
                if any(self.party_agent.get_party_members_in_combat()):
                    monster_target_coord = self.party_agent.get_party_members_in_combat()[0].coord
                    self.dark_event_service.pass_time(GlobalLocation(COMBAT_MAP_LOCATION_INDEX, 0, monster_target_coord))

        self.log(f"Exiting combat with {enemy_npc.name}")

        for party_member in self.party_agent.get_party_members_in_combat():
            party_member.exit_combat()

        self.party_agent.pop_location()

        # NPC unfreezing happens here.
        self.dark_event_service.pass_time(self.party_agent.get_current_location())

        self.npc_service.set_attacking_npc(None)
        self.npc_service.remove_npc(enemy_npc)





    