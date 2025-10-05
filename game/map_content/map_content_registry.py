from dark_libraries.dark_math import Coord

from maps.u5map import U5Map

from .coord_contents import CoordContents
from .map_level_contents import MapLevelContents

class MapContentRegistry:
    def __init__(self):
        self._contents: dict[tuple[int,int], MapLevelContents] = {}

    def add_u5map(self, u5_map: U5Map):
        for level_index in u5_map.levels.keys():
            self._contents[(u5_map.location_metadata.location_index, level_index)] = MapLevelContents(u5_map, level_index)
        print(f"[map_content_registry] Registered map {u5_map.location_metadata.name}")

    def get_coord_contents(self, location_index: int, level_index: int, coord: Coord) -> CoordContents:
        map_level_contents = self._contents[(location_index, level_index)]
        return map_level_contents.get_coord_contents(coord)
    
    def get_map_level_contents(self, location_index: int, level_index: int) -> MapLevelContents:
        return self._contents[(location_index, level_index)]
