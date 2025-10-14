from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from dark_libraries.dark_events import DarkEventListenerMixin

from models.agents.party_agent import PartyAgent
from models.global_location import GlobalLocation
from models.agents.npc_agent import NpcAgent

from services.map_cache.map_cache_service import MapCacheService

class NpcService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    map_cache_service: MapCacheService
    party_agent: PartyAgent

    def __init__(self):
        super().__init__()
        self._active_npcs: list[NpcAgent] = []
        self._frozen_npcs: list[NpcAgent] = []

        self._party_location: GlobalLocation = None
        self._attacking_npc: NpcAgent = None

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

        # Leaving the over/under world 
        if self._party_location.location_index == 0 and party_location.location_index != 0:
            self._freeze_active_npcs()
        
        # Returning to over/under world 
        if self._party_location.location_index != 0 and party_location.level_index == 0:
            self._unfreeze_active_npcs()
        
        #
        # TODO: Changing town/dungeon levels.
        #

        self._party_location = party_location

    def party_moved(self, party_location: GlobalLocation):
        self._party_location = party_location
    # IMPLEMENTATION END: DarkEventListenerMixin

    def get_npcs(self) -> dict[Coord, NpcAgent]:
        registered = {npc.coord: npc for npc in self._active_npcs}
        if self._party_location.location_index == 0:
            registered[self._party_location.coord] = self.party_agent
        return registered

    def add_npc(self, npc_agent: NpcAgent):
        self._active_npcs.append(npc_agent)

    def remove_npc(self, npc_agent: NpcAgent):
        self._active_npcs.remove(npc_agent)

    def get_attacking_npc(self) -> NpcAgent:
        return self._attacking_npc
    
    def set_attacking_npc(self, npc_agent: NpcAgent):
        self._attacking_npc = npc_agent

    def get_occupied_coords(self) -> set[Coord]:
        return {coord for coord in self.get_npcs().keys()}

