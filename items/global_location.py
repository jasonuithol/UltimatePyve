from typing import Self
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord

@immutable
@auto_init
class GlobalLocation:
    location_index: int
    level_index: int
    coord: Coord

    def __eq__(self, other: Self):
        return type(other) is GlobalLocation and self.location_index == other.location_index and self.level_index == other.level_index and self.coord == other.coord
    
    def __hash__(self):
        return hash((self.location_index, self.level_index, self.coord))
    
    def __str__(self):
        return f"location={self.location_index}, level={self.level_index}, coord={self.coord}"
    
    def __repr__(self):
        return self.__str__()
