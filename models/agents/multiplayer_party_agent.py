from dark_libraries.dark_math import Coord

from models.agents.npc_agent import NpcAgent
from models.global_location import GlobalLocation
from models.tile import Tile

class MultiplayerPartyAgent(NpcAgent):

    def __init__(self, name: str, dexterity: int, location: GlobalLocation):
        self._name = name
        self._dexterity = dexterity
        self._location: GlobalLocation = location
        self._multiplayer_id: int = None
    
    # NPC AGENT IMPLEMENTATION: Start
    #
    @property
    def tile_id(self) -> int:
        return 284

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_tile(self) -> Tile:
        #
        # TODO: Actually have a sprite etc
        #
        return 284

    @property
    def coord(self) -> Coord[int]:
        return self._location.coord
    
    @coord.setter
    def coord(self, value: Coord[int]):
        #
        # TODO: This may or may not require a network action
        #
        self._location = self._location.move_to_coord(value)

    @property
    def dexterity(self) -> int:
        return self._dexterity
    #
    # NPC AGENT IMPLEMENTATION: End

    @property
    def location_index(self) -> int:
        return self._location.location_index
    
    @property
    def level_index(self) -> int:
        return self._location.level_index
    
    @property
    def location_index(self) -> int:
        return self._location.location_index
    
    @property
    def location(self) -> int:
        return self._location
    
    @location.setter
    def location(self, value: int):
        self._location = value

    @property
    def multiplayer_id(self) -> int:
        return self._multiplayer_id
    
    @multiplayer_id.setter
    def multiplayer_id(self, value: int):
        self._multiplayer = value
