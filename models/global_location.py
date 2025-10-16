from typing import Self
from dark_libraries.custom_decorators import immutable
from dark_libraries.dark_math import Coord
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX

@immutable
class GlobalLocation:
    def __init__(self, location_index: int, level_index: int, coord: Coord):

        assert not coord is None, "coord cannot be None"

        self._location_index = location_index
        self._level_index = level_index
        self._coord = coord

    @property
    def location_index(self) -> int:
        return self._location_index

    @property
    def level_index(self) -> int:
        return self._level_index

    @property
    def coord(self) -> Coord:
        return self._coord

    def __eq__(self, other: Self):
        return type(other) is GlobalLocation and self.location_index == other.location_index and self.level_index == other.level_index and self.coord == other.coord
    
    def __hash__(self):
        return hash((self.location_index, self.level_index, self.coord))
    
    def __str__(self):
        return f"location={self.location_index}, level={self.level_index}, coord={self.coord}"
    
    def __repr__(self):
        return self.__str__()
    
    def __add__(self, offset: tuple[int,int]) -> Self:
        return __class__(self.location_index, self.level_index, self.coord + offset)

    def is_in_town(self) -> bool:
        return 1 <= self.location_index < 27
    
    def is_combat(self) -> bool:
        return self.location_index == COMBAT_MAP_LOCATION_INDEX

    def move_to_coord(self, coord: Coord) -> Self:
        return GlobalLocation(
            self._location_index,
            self._level_index,
            coord
        )
    
    def move_to_level(self, level_index: int) -> Self:
        return GlobalLocation(
            self._location_index,
            level_index,
            self._coord
        )