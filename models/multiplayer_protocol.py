from typing import NamedTuple
from dark_libraries.dark_math import Coord
from models.global_location import GlobalLocation

def _get_coord(self):
    return Coord(self.x, self.y)

def _get_location(self):
    return GlobalLocation(
        self.location_index,
        self.level_index,
        _get_coord(self)
    )

class ConnectRequest(NamedTuple):
    name: str
    tile_id: int
    dexterity: int

    location_index: int
    level_index: int
    x: int 
    y: int

    get_coord = _get_coord
    get_location = _get_location

class ConnectAccept(NamedTuple):
    multiplayer_id: str
    x: int
    y: int

    get_coord = _get_coord

class ConnectTerminate(NamedTuple):
    pass

class PlayerJoin(NamedTuple):
    name: str
    tile_id: int
    dexterity: int
    multiplayer_id: str

    location_index: int
    level_index: int
    x: int 
    y: int

    get_coord = _get_coord
    get_location = _get_location

class PlayerLeave(NamedTuple):
    multiplayer_id: str
    
class LocationUpdate(NamedTuple):
    multiplayer_id: str
    tile_id: int

    location_index: int
    level_index: int
    x: int
    y: int

    get_coord = _get_coord
    get_location = _get_location
