from dark_libraries.dark_math import Coord
from .light_map import LightMap

class LightMapRegistry:
    def _after_inject(self):
        self.maximum_radius = 0
        self.light_maps: dict[int, LightMap] = {}
        self.baked_light_maps: dict[tuple[int, int], dict[Coord, LightMap]] = {}
    
    def register_light_map(self, radius: int, light_map: LightMap):
        assert len(light_map) > 0, "Probably DON'T want to register an empty light map ?"
        self.light_maps[radius] = light_map
        self.maximum_radius = max(self.maximum_radius, radius)

    def register_baked_light_map(self, location_index: int, level: int, world_coord: Coord, baked_light_map: LightMap):
        key = location_index, level
        if not key in self.baked_light_maps.keys():
            self.baked_light_maps[key] = {}
        self.baked_light_maps[key][world_coord] = baked_light_map    

    def get_light_map(self, radius: int) -> LightMap:
        return self.light_maps[radius]
    
    def get_maximum_radius(self):
        return self.maximum_radius

    def get_baked_light_maps(self, location_index: int, level: int) -> dict[Coord, LightMap]:
        return self.baked_light_maps.get((location_index, level),None)