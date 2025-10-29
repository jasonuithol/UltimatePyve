import random
from dark_libraries.dark_math   import Coord
from dark_libraries.logging     import LoggerMixin
from dark_libraries.dark_events import DarkEventListenerMixin

from models.agents.monster_agent import MonsterAgent
from models.agents.party_agent import PartyAgent
from models.agents.party_member_agent import PartyMemberAgent
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX
from models.global_location    import GlobalLocation
from models.agents.npc_agent   import NpcAgent

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
        if self._party_location.location_index != 0 and party_location.location_index == 0:
            self._unfreeze_active_npcs()
        
        #
        # TODO: Changing town/dungeon levels.
        #

        self._party_location = party_location

    def party_moved(self, party_location: GlobalLocation):
        self._party_location = party_location
    # IMPLEMENTATION END: DarkEventListenerMixin

    def get_npcs(self) -> dict[Coord[int], NpcAgent]:
        registered = {npc.coord: npc for npc in self._active_npcs}
        if self._party_location.location_index != COMBAT_MAP_LOCATION_INDEX:
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

    def get_npc_at(self, coord: Coord) -> NpcAgent | None:
        return self.get_npcs().get(coord, None)

    def get_occupied_coords(self) -> set[Coord]:
        return {coord for coord in self.get_npcs().keys()}

    def get_next_moving_npc(self) -> NpcAgent | None:
        if not any(self._active_npcs):
            return None

        candidates = self.get_npcs().values()

        min_spent_action_points = min(npc.spent_action_points for npc in candidates)
        ap_candidates = [npc for npc in candidates if npc.spent_action_points == min_spent_action_points]

        if not any(ap_candidates):
            return None
        
        max_dexterity = max(npc.dexterity for npc in ap_candidates)
        dex_candidates = [npc for npc in ap_candidates if npc.dexterity == max_dexterity]

        if not any(dex_candidates):
            return None
        
        final_choice = random.choice(dex_candidates)
        self.log(
            f"DEBUG: Choosing {final_choice.name} at {final_choice.coord} with {final_choice.spent_action_points} spent action points for next turn"
            +
            f", out of {len(ap_candidates)} action candidates and {len(dex_candidates)} DEX candidates."
        )

        if final_choice.slept:
            if random.randint(0,100) < 2:
                self.log(f"awakening eepy-deepy ({final_choice.name}), but still choosing next npc for an action")
                final_choice.awake()
            else:
                self.log(f"eepy-deepy detected ({final_choice.name}), choosing next npc for an action")

            final_choice.spend_action_quanta()
            return self.get_next_moving_npc()
        else:
            return final_choice

    def get_party_members(self) -> list[PartyMemberAgent]:
        return [npc for npc in self._active_npcs if isinstance(npc, PartyMemberAgent)]

    def get_party_member_count(self) -> int:
        return sum(1 for npc in self._active_npcs if isinstance(npc, PartyMemberAgent))

    def get_monsters(self) -> list[MonsterAgent]:
        return [npc for npc in self._active_npcs if isinstance(npc, MonsterAgent)]

    def get_monster_count(self) -> int:
        return sum(1 for npc in self._active_npcs if isinstance(npc, MonsterAgent))
    
