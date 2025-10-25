# file: game/u5map.py
from typing import Iterable
from dark_libraries.dark_math import Coord, Size

from models.u5_map_level      import U5MapLevel
from models.location_metadata import LocationMetadata

class U5Map(tuple):

    def __new__(cls, levels: dict[int, U5MapLevel], location_metadata: LocationMetadata):
        size = cls._get_first_map(levels).get_size()

        return tuple.__new__(cls, (levels, location_metadata, size))

    @classmethod
    def _get_first_map(cls, levels: dict[int, U5MapLevel]) -> U5MapLevel:
        key = next(levels.keys().__iter__())
        return levels[key]

    @property
    def _levels(self) -> dict[int, U5MapLevel]:
        return self[0]

    @property
    def _location_metadata(self) -> LocationMetadata:
        return self[1]

    def get_size(self) -> Size[int]:
        return self[2]

    @property
    def location_index(self) -> int:
        return self._location_metadata.location_index
 
    @property
    def name(self) -> str:
        return self._location_metadata.name

    @property
    def default_level_index(self) -> int:
        return self._location_metadata.default_level

    def get_map_level(self, level_index: int) -> U5MapLevel:
        assert level_index in self._levels.keys(), f"Unknown level_index {level_index} for map {self.name} (known keys={self._levels.keys()})"
        return self._levels[level_index]

    def get_level_indexes(self) -> list[int]:
        return list(self._levels.keys())

    def is_in_bounds(self, coord: Coord[int]) -> bool:
        return self.get_size().is_in_bounds(coord)

    def get_wrapped_coord(self, coord: Coord[int]) -> Coord[int]:
        return Coord[int](coord.x % self.get_size().x, coord.y % self.get_size().y)

    def get_tile_id(self, level_index: int, coord: Coord[int]) -> int:
        map_level = self.get_map_level(level_index)
        return map_level.get_tile_id(coord)

    def get_coord_iteration(self) -> Iterable[Coord[int]]:
        return __class__._get_first_map(self._levels).coords()

    def render_to_disk(self):
        for level_index, map_level in self._levels.items():
            map_level.render_to_disk(f"{self.name}_{level_index}")

    def __iter__(self) -> Iterable[tuple[int, U5MapLevel]]:
        yield from self._levels.items()

