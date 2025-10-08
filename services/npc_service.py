from dark_libraries.dark_math import Coord

from services.map_cache.map_cache_service import MapCacheService

from models.npc_agent import NpcAgent
from services.map_cache.map_level_contents import MapLevelContents

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

        map_level_contents: MapLevelContents  = self.map_cache_service.get_map_level_contents(self.location_index, self.level_index)

        blocked_coords: set[Coord] = {
            coord
            # TODO: make a method for this ?
            for coord, coord_content in map_level_contents
            if coord_content.get_terrain().walk == True
        }

        occupied_coords = {npc.get_coord() for npc in self.active_npcs}
        occupied_coords.add(self.player_coord)

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

