from dark_libraries.dark_math import Coord

from dark_libraries.dark_network import DarkNetworkClient
from models.agents.npc_agent import NpcAgent
from models.global_location import GlobalLocation
from models.tile import Tile

class MultiplayerPartyAgent(NpcAgent):

    def __init__(self, name: str, dexterity: int):
        self._name = name
        self._dexterity = dexterity

        self._current_tile_id: int = None
        self._location: GlobalLocation = None

        self._slept: bool = None
    
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
        return self._current_tile_id

    @property
    def coord(self) -> Coord[int]:
        return self._location.coord
    
    @coord.setter
    def coord(self, value: Coord[int]):
        self._location = self._location.move_to_coord(value)

    @property
    def dexterity(self) -> int:
        return self._dexterity

    @property
    def slept(self) -> bool:
        return self._slept
    #
    # NPC AGENT IMPLEMENTATION: End