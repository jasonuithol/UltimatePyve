from typing import Self
from dark_libraries.dark_math import Coord
from models.enums.combat_map_location_index import COMBAT_MAP_LOCATION_INDEX

class GlobalLocation(tuple):
    __slots__ = ()

    def __new__(cls, location_index: int, level_index: int, coord: Coord):
        assert not coord is None, "coord cannot be None"
        return tuple.__new__(cls, (location_index, level_index, coord))

    @property
    def location_index(self) -> int:
        return self[0]

    @property
    def level_index(self) -> int:
        return self[1]

    @property
    def coord(self) -> Coord:
        return self[2]
    
    def __add__(self, offset: tuple[int,int]) -> Self:
        return __class__(self.location_index, self.level_index, self.coord + offset)

    #
    # TODO: Remove
    #
    def is_in_town(self) -> bool:
        return 1 <= self.location_index < 27

    def move_to_coord(self, coord: Coord) -> Self:
        return GlobalLocation(
            self.location_index,
            self.level_index,
            coord
        )
    
    def move_to_level(self, level_index: int) -> Self:
        return GlobalLocation(
            self.location_index,
            level_index,
            self.coord
        )