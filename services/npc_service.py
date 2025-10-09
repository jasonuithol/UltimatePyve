from dark_libraries.dark_math import Coord

from models.npc_agent import NpcAgent

from services.map_cache.map_cache_service  import MapCacheService

class NpcService:

    # Injectable
    map_cache_service: MapCacheService

    def _after_inject(self):
        self._active_npcs: list[NpcAgent] = []
        self._frozen_npcs: list[NpcAgent] = []

        self._location_index = None
        self._level_index = None

    def _freeze_active_npcs(self):
        self._frozen_npcs = self._active_npcs
        self._active_npcs = []

    def _unfreeze_active_npcs(self):
        self._active_npcs = self._frozen_npcs
        self._frozen_npcs = []

    def load_level(self, location_index: int, level_index: int):

        # Leaving the over/under world 
        if self._location_index == 0 and location_index != 0:
            self._freeze_active_npcs()
        
        # Returning to over/under world 
        if self._location_index != 0 and location_index == 0:
            self._unfreeze_active_npcs()
        
        #
        # TODO: Changing town/dungeon levels.
        #

        self._location_index = location_index
        self._level_index = level_index

    def set_player_coord(self, player_coord: Coord):
        self.player_coord = player_coord


    def get_npcs(self) -> dict[Coord, NpcAgent]:
        return {npc.get_coord(): npc for npc in self._active_npcs}

    def add_npc(self, npc_agent: NpcAgent):
        self._active_npcs.append(npc_agent)

    def remove_npc(self, npc_agent: NpcAgent):
        self._active_npcs.remove(npc_agent)

    def get_occupied_coords(self) -> set[Coord]:
        return {npc.get_coord() for npc in self._active_npcs}.union({self.player_coord})

