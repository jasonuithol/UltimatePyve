from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from dark_libraries.dark_events import DarkEventListenerMixin

from models.global_location import GlobalLocation
from models.npc_agent import NpcAgent

from services.map_cache.map_cache_service import MapCacheService

class NpcService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    map_cache_service: MapCacheService

    def _after_inject(self):
        super()._after_inject()

        self._active_npcs: list[NpcAgent] = []
        self._frozen_npcs: list[NpcAgent] = []

        self._party_location: GlobalLocation = None

    def _freeze_active_npcs(self):
        self.log(f"Freezing {len(self._active_npcs)} NPCs.")
        self._frozen_npcs = self._active_npcs
        self._active_npcs = []

    def _unfreeze_active_npcs(self):
        self.log(f"Unfreezing {len(self._frozen_npcs)} NPCs.")
        self._active_npcs = self._frozen_npcs
        self._frozen_npcs = []

    # IMPLEMENTATION START: DarkEventListenerMixin
    def loaded(self, party_location: GlobalLocation):
        self._party_location = party_location

    def level_changed(self, party_location: GlobalLocation):

        self._party_location = party_location

        # Leaving the over/under world 
        if self._party_location.location_index == 0 and party_location.level_index != 0:
            self._freeze_active_npcs()
        
        # Returning to over/under world 
        if self._party_location.location_index != 0 and party_location.level_index == 0:
            self._unfreeze_active_npcs()
        
        #
        # TODO: Changing town/dungeon levels.
        #

    def party_moved(self, party_location: GlobalLocation):
        self._party_location = party_location
    # IMPLEMENTATION END: DarkEventListenerMixin

    def get_npcs(self) -> dict[Coord, NpcAgent]:
        return {npc.get_coord(): npc for npc in self._active_npcs}

    def add_npc(self, npc_agent: NpcAgent):
        self._active_npcs.append(npc_agent)

    def remove_npc(self, npc_agent: NpcAgent):
        self._active_npcs.remove(npc_agent)

    def get_occupied_coords(self) -> set[Coord]:
        return {npc.get_coord() for npc in self._active_npcs}.union({self._party_location.coord})

