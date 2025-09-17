from typing import Self
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord

@immutable
@auto_init
class GlobalLocation:
    location_index: int
    level: int
    coord: Coord

    def __eq__(self, other: Self):
        return type(other) is GlobalLocation and self.location_index == other.location_index and self.level == other.level and self.coord == other.coord
    
    def __hash__(self):
        return hash((self.location_index, self.level, self.coord))
    
    def __str__(self):
        return f"location={self.location_index}, level={self.level}, coord={self.coord}"
    
    def __repr__(self):
        return self.__str__()
