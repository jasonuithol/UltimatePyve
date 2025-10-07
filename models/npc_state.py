from typing import Protocol

from dark_libraries.dark_math import Coord
from dark_libraries.service_provider import ServiceProvider

from data.global_registry import GlobalRegistry
from models.global_location import GlobalLocation


class NpcState(Protocol):
    def __init__(self, global_location: GlobalLocation):

        self.global_location = global_location
        self.global_registry: GlobalRegistry = ServiceProvider.get_provider().resolve(GlobalRegistry)

    def get_coord(self) -> Coord:
        return self.global_location.coord
    
    def pass_time(self, blocked_coords: set[Coord], player_coord: Coord):
        ...
