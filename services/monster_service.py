
import random
import pygame

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math   import Coord
from dark_libraries.logging     import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.npc_agent                import NpcAgent
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
from models.enums.projectile_type           import ProjectileType
from models.enums.transport_mode import TransportMode
from models.global_location                 import GlobalLocation
from models.agents.monster_agent            import MonsterAgent
from models.u5_map                          import U5Map

from services.console_service             import ConsoleService
from services.display_service             import DisplayService
from services.info_panel_service          import InfoPanelService
from services.input_service               import InputService
from services.npc_service                 import NpcService
from services.map_cache.map_cache_service import MapCacheService
from services.sfx_library_service         import SfxLibraryService

RANGED_ATTACK_CHANCE = 0.20
DO_NOTHING_CHANCE    = 0.05

MONSTER_THOUGHT_SECS = 0.25

class MonsterService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    global_registry:     GlobalRegistry

    console_service:     ConsoleService
    map_cache_service:   MapCacheService
    npc_service:         NpcService
    display_service:     DisplayService
    input_service:       InputService
    sfx_library_service: SfxLibraryService
    info_panel_service:  InfoPanelService

    def take_combat_turn(self, monster_agent: MonsterAgent):

        assert not monster_agent.slept, "Cannot give a sleeping monster a turn."

        self.log(f"DEBUG: {monster_agent.name} ranged_attacks ? {monster_agent._npc_metadata.abilities_attack.has_ranged_attack()}")

        # Let's simulate the monster taking a real-world-time moment to think about what it's going to do.
        decision_time = pygame.time.get_ticks() + (MONSTER_THOUGHT_SECS * 1000)
        while pygame.time.get_ticks() < decision_time:
            self.display_service.render()
            self.input_service.discard_events()

        active_party_members = self.npc_service.get_party_members()

        distances = {
            monster_agent.coord.pythagorean_distance(party_member.coord) : party_member
            for party_member in active_party_members
        }

        shortest_distance = min(distances.keys())
        closest_party_member = distances[shortest_distance]

        dice_roll = random.randint(0, 100)

        if dice_roll < RANGED_ATTACK_CHANCE * 100 and monster_agent._npc_metadata.abilities_attack.has_ranged_attack():
            self.log(f"DEBUG: {monster_agent.name} performing ranged attack on {closest_party_member.name}")
            self.sfx_library_service.emit_projectile(
                ProjectileType.MagicMissile,
                monster_agent.coord,
                closest_party_member.coord
            )
            hit_success = monster_agent.attack(closest_party_member, weapon = None)
            if hit_success:
                self.sfx_library_service.damage(closest_party_member.coord)
                self.info_panel_service.update_party_summary()
                self.console_service.print_ascii(f"{closest_party_member.name} hit !")

        #
        # DO NOTHING
        #
        elif dice_roll < (RANGED_ATTACK_CHANCE + DO_NOTHING_CHANCE) * 100:
            self.log(f"DEBUG: {monster_agent.name} standing there like a stunned mullet")

        #
        # MELEE ATTACK
        #
        elif closest_party_member.coord in monster_agent.coord.get_8way_neighbours():
            self.log(f"DEBUG: {monster_agent.name} performing melee attack on {closest_party_member.name}")
            hit_success = monster_agent.attack(closest_party_member, weapon = None)
            if hit_success:
                self.sfx_library_service.damage(closest_party_member.coord)
                self.info_panel_service.update_party_summary()
                self.console_service.print_ascii(f"{closest_party_member.name} hit !")
            else:
                self.sfx_library_service.miss()

        #
        # MOVE
        #
        else:
            self.log(f"DEBUG: {monster_agent.name} moving towards {closest_party_member.name}")

            #
            # TODO: get the terrain type of the monster to get real transport mode index
            #
            forbidden_coords = self.map_cache_service.get_blocked_coords(COMBAT_MAP_LOCATION_INDEX, 0, transport_mode = TransportMode.WALK) | self.npc_service.get_occupied_coords()

            combat_map: U5Map = self.global_registry.maps.get(COMBAT_MAP_LOCATION_INDEX)
            monster_agent.move_towards(closest_party_member.coord, forbidden_coords, combat_map.get_size().to_rect(Coord[int](0, 0)))


        if closest_party_member.hitpoints == 0:
            self.console_service.print_ascii(f"{closest_party_member.name} killed !")
            self.npc_service.remove_npc(closest_party_member)
            closest_party_member._character_record.status = "D" # TODO: Not showing up in info_panel ???
            self.info_panel_service.update_party_summary()

        # use up their current action points
        monster_agent.spend_action_quanta()

    #
    # TODO: In combat mode: "party_location" is really the combat map coord of the avatar.
    #       This allows pathing to the avatar to simulate AI attack strategies, but falls  
    #       apart whenever a monster gets in range of any party member that isn't the
    #       actual avatar
    #
    def pass_time(self, party_location: GlobalLocation):

        if party_location.location_index == COMBAT_MAP_LOCATION_INDEX:
            self.log("DEBUG: Ignoring pass_time event whilst in combat.")
            return

        super().pass_time(party_location)

        blocked_coords = self.map_cache_service.get_blocked_coords(
            party_location.location_index, 
            party_location.level_index, 
            transport_mode = TransportMode.WALK
        )

        current_map = self.global_registry.maps.get(party_location.location_index)
        current_boundary_rect = current_map.get_size() if current_map.location_index != 0 else None

        occupied_coords = self.npc_service.get_occupied_coords()

        # Find all the monsters up for a turn, and give them a turn.
        next_npc_agent: NpcAgent = self.npc_service.get_next_moving_npc()
        while isinstance(next_npc_agent, MonsterAgent):

            monster_agent: MonsterAgent = next_npc_agent
                    
            old_coord = monster_agent.coord

            if monster_agent.coord.taxi_distance(party_location.coord) == 1:
                self.npc_service.set_attacking_npc(monster_agent)
            else:
                #
                # TODO: Monster Party might attempt a ranged attack
                #
                monster_agent.move_towards(
                    target_coord     = party_location.coord,
                    forbidden_coords = blocked_coords.union(occupied_coords),
                    boundary_rect    = current_boundary_rect
                )

            new_coord = monster_agent.coord

            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                if old_coord in occupied_coords:
                    occupied_coords.remove(old_coord)

            monster_agent.spend_action_quanta()

            next_npc_agent: NpcAgent = self.npc_service.get_next_moving_npc()


