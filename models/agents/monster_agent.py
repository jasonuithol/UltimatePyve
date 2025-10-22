from dark_libraries.dark_math import Coord

from models.agents.combat_agent import CombatAgent
from models.npc_metadata        import NpcMetadata
from models.sprite              import Sprite
from models.tile import Tile

from .combat_agent import CombatAgent

class MonsterAgent(CombatAgent):
    
    def __init__(self, coord: Coord, sprite: Sprite[Tile], npc_metadata: NpcMetadata):
        super().__init__(coord, sprite)
        self._npc_metadata = npc_metadata
        self._current_hitpoints = self.maximum_hitpoints

    # NPC_AGENT IMPLEMENTATION (Completion): Start
    #
    @property
    def tile_id(self) -> int:
        return self._npc_metadata.npc_tile_id

    @property
    def name(self) -> str:
        return self._npc_metadata.name

    @property
    def dexterity(self) -> int:
        return self._npc_metadata.dexterity
    #
    # NPC_AGENT IMPLEMENTATION (Completion): End

    # COMBAT_AGENT IMPLEMENTATION: Start
    #
    @property
    def strength(self) -> int:
        return self._npc_metadata.strength

    @property
    def armour(self) -> int:
        return self._npc_metadata.armour

    @property
    def maximum_hitpoints(self) -> int:
        return self._npc_metadata.hitpoints

    @property 
    def hitpoints(self) -> int:
        return self._current_hitpoints

    @hitpoints.setter
    def hitpoints(self, val: int):
        self._current_hitpoints = val

    def get_damage(self, attack_type: chr) -> int:
        if self._npc_metadata.damage == 0:
            self.log(f"ERROR: monster {self.name} has zero damage")
        return self._npc_metadata.damage
    #
    # COMBAT_AGENT IMPLEMENTATION: End

        
