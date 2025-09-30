import math
from dark_libraries.dark_math import Coord
from display.display_config import DisplayConfig

LightMap = dict[Coord, int]

class LightMapRegistry:
    def _after_inject(self):
        self.maximum_radius = 0
        self.light_maps: dict[int, LightMap] = {}
    
    def register_light_map(self, radius: int, light_map: LightMap):
        self.light_maps[radius] = light_map
        self.maximum_radius = max(self.maximum_radius, radius)

    def get_light_map(self, radius: int) -> LightMap:
        return self.light_maps[radius]
    
    def get_maximum_radius(self):
        return self.maximum_radius

class LightMapBuilder:

    # Injectable
    display_config: DisplayConfig
    light_map_registry: LightMapRegistry
    
    def build_light_maps(self):
        max_dimension_size = max(self.display_config.VIEW_PORT_SIZE.w, self.display_config.VIEW_PORT_SIZE.h)
        max_lit_tiles = self.display_config.VIEW_PORT_SIZE.w * self.display_config.VIEW_PORT_SIZE.h

        # We need to draw radii right up to the corners, extending beyond the viewport in the extreme cases.
        # so calculate the max radius using the tile diagonals, not the tile horiz/vert sizes.
        max_radius = math.ceil(max_dimension_size * (2 ** 0.5))

        centre = Coord(self.display_config.VIEW_PORT_SIZE.w // 2, self.display_config.VIEW_PORT_SIZE.h // 2)
        for radius in range(1, max_radius + 1):
            light_map = LightMap()
            for view_coord in self.display_config.VIEW_PORT_SIZE:
                distance = int(abs(((view_coord.x - centre.x) ** 2) + ((view_coord.y - centre.y) ** 2)) ** 0.5)
                is_lit = (distance <= radius)
                light_map[view_coord] = is_lit
            self.light_map_registry.register_light_map(radius, light_map)
            num_lit_tiles = sum([light_value for light_value in light_map.values()])
            print(f"[lighting] Built LightMap for radius {radius} with {num_lit_tiles} lit tiles.")
            if num_lit_tiles == max_lit_tiles:
                print(f"[lighting] Maximum lit tiles of {max_lit_tiles} reached at radius {radius}, terminating light map generation.")
                break
        print(f"[lighting] Registered {len(self.light_map_registry.light_maps)} light maps.")
    