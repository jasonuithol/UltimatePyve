# file: game/u5map.py
from typing import Iterable
from dark_libraries.custom_decorators import immutable
from dark_libraries.dark_math         import Coord, Size

from models.u5_map_level      import U5MapLevel
from models.location_metadata import LocationMetadata

@immutable
class U5Map:

    def __init__(self, levels: dict[int, U5MapLevel], location_metadata: LocationMetadata):
        self._levels = levels
        self._location_metadata = location_metadata
        self._size = self._get_first_map().get_size()

    @property
    def name(self) -> str:
        return self._location_metadata.name

    @property
    def location_index(self) -> int:
        return self._location_metadata.location_index
    
    @property
    def default_level_index(self) -> int:
        return self._location_metadata.default_level

    def _get_first_map(self) -> U5MapLevel:
        key = next(self._levels.keys().__iter__())
        return self._levels[key]

    def get_size(self) -> Size:
        return self._size
    
    def get_map_level(self, level_index: int) -> U5MapLevel:
        assert level_index in self._levels.keys(), f"Unknown level_index {level_index} for map {self.name} (known keys={self._levels.keys()})"
        return self._levels[level_index]

    def get_level_indexes(self) -> set[int]:
        return self._levels.keys()

    def is_in_bounds(self, coord: Coord) -> bool:
        return self.get_size().is_in_bounds(coord)

    def get_wrapped_coord(self, coord: Coord) -> Coord:
        return Coord(coord.x % self.get_size().x, coord.y % self.get_size().y)

    def get_tile_id(self, level_index: int, coord: Coord) -> int:
        map_level = self.get_map_level(level_index)
        return map_level.get_tile_id(coord)

    def get_coord_iteration(self) -> Iterable[Coord]:
        return self._get_first_map().coords()

    def render_to_disk(self):
        for level_index, map_level in self._levels.items():
            map_level.render_to_disk(f"{self.name}_{level_index}")

    def __iter__(self) -> Iterable[tuple[int, U5MapLevel]]:
        yield from self._levels.items()

