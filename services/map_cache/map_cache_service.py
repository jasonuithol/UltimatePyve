from typing import Protocol
from dark_libraries.dark_math import Coord

from models.enums.transport_mode import TransportMode
from models.global_location import GlobalLocation
from models.u5_map  import U5Map

from services.map_cache.coord_contents     import CoordContents
from services.map_cache.map_level_contents import MapLevelContents

class MapCacheService(Protocol):

    # Call this AFTER mods have loaded.
    def init(self): ...

    def cache_u5map(self, u5_map: U5Map): ...
    def get_location_contents(self, global_location: GlobalLocation) -> CoordContents: ...
    def get_map_level_contents(self, location_index: int, level_index: int) -> MapLevelContents: ...
    def get_blocked_coords(self, location_index: int, level_index: int, transport_mode: TransportMode) -> set[Coord[int]]: ...
