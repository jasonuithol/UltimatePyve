from dark_libraries.dark_math import Coord

from models.npc_agent import NpcAgent

from services.map_cache.map_cache_service  import MapCacheService

class NpcService:

    # Injectable
    map_cache_service: MapCacheService

    def _after_inject(self):
        self.active_npcs: list[NpcAgent] = []
        self.frozen_npcs: list[NpcAgent] = None

    def _freeze_active_npcs(self):
        self.frozen_npcs = self.active_npcs
        self.active_npcs = []

    def _unfreeze_active_npcs(self):
        self.active_npcs = self.frozen_npcs
        self.frozen_npcs = []

    def load_level(self, location_index: int, level_index: int):
        self.location_index = location_index
        self.level_index = level_index

    def set_player_coord(self, player_coord: Coord):
        self.player_coord = player_coord

    def pass_time(self):
        blocked_coords = self.map_cache_service.get_blocked_coords(self.location_index, self.level_index, transport_mode_index = 0)
        occupied_coords = self.get_occupied_coords()

        # Give all the NPCs a turn.
        for npc in self.active_npcs:
            old_coord = npc.get_coord()
            npc.pass_time(blocked_coords.union(occupied_coords), self.player_coord)
            new_coord = npc.get_coord()
            if old_coord != new_coord:
                occupied_coords.add(new_coord)
                occupied_coords.remove(old_coord)

    def get_npcs(self) -> dict[Coord, NpcAgent]:
        return {npc.get_coord(): npc for npc in self.active_npcs}

    def add_npc(self, npc_agent: NpcAgent):
        self.active_npcs.append(npc_agent)

    def remove_npc(self, npc_agent: NpcAgent):
        self.active_npcs.remove(npc_agent)

    def get_occupied_coords(self) -> set[Coord]:
        return {npc.get_coord() for npc in self.active_npcs}.union({self.player_coord})

