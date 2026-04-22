from typing import Iterable

from dark_libraries.dark_math import Coord

from services.map_cache.coord_contents import CoordContents

class MapLevelContents:

    def __init__(self, coord_contents_dict: dict[Coord[int], CoordContents]):
        self._coord_contents_dict = coord_contents_dict

    def get_coord_contents(self, coord: Coord[int]) -> CoordContents:
        return self._coord_contents_dict.get(coord, None)

    def __iter__(self) -> Iterable[tuple[Coord[int], CoordContents]]:
        return self._coord_contents_dict.items().__iter__()
