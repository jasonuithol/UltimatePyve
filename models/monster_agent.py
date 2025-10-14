from models.global_location import GlobalLocation
from models.npc_metadata    import NpcMetadata
from models.npc_agent       import NpcAgent
from models.sprite          import Sprite

class MonsterAgent(NpcAgent):
    
    def __init__(self, sprite: Sprite, global_location: GlobalLocation, npc_metadata: NpcMetadata):
        super().__init__(sprite, global_location)
        self._npc_metadata = npc_metadata
        self._current_hitpoints = self.maximum_hitpoints

    # NPC_AGENT IMPLEMENTATION: Start
    @property
    def tile_id(self) -> int:
        return self._npc_metadata.npc_tile_id

    @property
    def name(self) -> str:
        return self._npc_metadata.name

    @property
    def strength(self) -> int:
        return self._npc_metadata.strength

    @property
    def dexterity(self) -> int:
        return self._npc_metadata.dexterity

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
        return self._npc_metadata.damage
    # NPC_AGENT IMPLEMENTATION: End

        
