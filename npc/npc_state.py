from typing import Protocol

from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider

from items.global_location import GlobalLocation
from maps.u5map_registry import U5MapRegistry


class NpcState(Protocol):
    def __init__(self, global_location: GlobalLocation):

        self.global_location = global_location
        self.u5_map_registry: U5MapRegistry = ServiceProvider.get_provider().resolve(U5MapRegistry)

    def get_coord(self) -> Coord:
        return self.global_location.coord
    
    def pass_time(self, blocked_coords: set[Coord], player_coord: Coord):
        ...
