
from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging     import LoggerMixin

from data.global_registry import GlobalRegistry

from models.agents.npc_agent import NpcAgent
from models.global_location      import GlobalLocation
from models.agents.monster_agent import MonsterAgent

from services.console_service             import ConsoleService
from services.npc_service                 import NpcService
from services.map_cache.map_cache_service import MapCacheService

class MonsterService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    console_service:   ConsoleService
    map_cache_service: MapCacheService
    npc_service:       NpcService
    global_registry:   GlobalRegistry

    def pass_time(self, party_location: GlobalLocation):
        super().pass_time(party_location)

        blocked_coords = self.map_cache_service.get_blocked_coords(
            party_location.location_index, 
            party_location.level_index, 
            transport_mode_index = 0
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
                # Combat map mode
                if current_map.location_index == -666:
                    self.console_service.print_ascii("WHAM !")

                # Overworld mode
                elif self.npc_service.get_attacking_npc() is None:
                    self.npc_service.set_attacking_npc(monster_agent)
            else:
                monster_agent.move_towards(
                    target_coord     = party_location.coord,
                    forbidden_coords = blocked_coords.union(occupied_coords),
                    boundary_rect    = current_boundary_rect
                )

            new_coord = monster_agent.coord

            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                occupied_coords.remove(old_coord)

            monster_agent.spend_action_quanta()

            next_npc_agent: NpcAgent = self.npc_service.get_next_moving_npc()


