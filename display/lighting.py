import math
from typing import Self
from dark_libraries.dark_math import Coord
from display.display_config import DisplayConfig
from game.terrain.terrain_registry import TerrainRegistry
from maps.u5map_registry import U5MapRegistry

class LightMap(set[Coord]):

    def copy(self) -> Self:
        return self.__class__(super().copy())

    def is_lit(self, coord: Coord) -> bool:
        return coord in self

    def light(self, coord: Coord):
        # will silently ignore duplicate coords, which is perfect.
        self.add(coord)

    def bake_level_light_map(self, level_light_map: Self, light_emitter_level_coord: Coord):
        for view_port_coord in self:
            # view_port_coord starts at 0,0 relative to the view_port.
            # light_emitter_coord is relative to the level map coords.
            level_light_map_coord = view_port_coord.add(light_emitter_level_coord)
            level_light_map.light(level_light_map_coord)

class LightMapRegistry:
    def _after_inject(self):
        self.maximum_radius = 0
        self.light_maps: dict[int, LightMap] = {}
        self.baked_light_maps: dict[tuple[int, int], LightMap] = {}
    
    def register_light_map(self, radius: int, light_map: LightMap):
        self.light_maps[radius] = light_map
        self.maximum_radius = max(self.maximum_radius, radius)

    def register_baked_light_map(self, location_index: int, level: int, baked_light_map: LightMap):
        self.baked_light_maps[location_index, level] = baked_light_map

    def get_light_map(self, radius: int) -> LightMap:
        return self.light_maps[radius]
    
    def get_maximum_radius(self):
        return self.maximum_radius

    def get_baked_light_map(self, location_index: int, level: int) -> LightMap:
        return self.baked_light_maps[location_index, level]

class LightMapBuilder:

    # Injectable
    display_config: DisplayConfig
    light_map_registry: LightMapRegistry
    
    # all unbaked light maps are built in coords relative to the light emitter.
    def build_light_maps(self):
        max_dimension_size = max(self.display_config.VIEW_PORT_SIZE.w, self.display_config.VIEW_PORT_SIZE.h)
        max_lit_tiles = self.display_config.VIEW_PORT_SIZE.w * self.display_config.VIEW_PORT_SIZE.h

        # We need to draw radii right up to the corners, extending beyond the viewport in the extreme cases.
        # so calculate the max radius using the tile diagonals, not the tile horiz/vert sizes.
        max_radius = math.ceil(max_dimension_size * (2 ** 0.5))

        light_emitter_coord = Coord(self.display_config.VIEW_PORT_SIZE.w // 2, self.display_config.VIEW_PORT_SIZE.h // 2)
        for radius in range(1, max_radius + 1):
            light_map = LightMap()
            for view_coord in self.display_config.VIEW_PORT_SIZE:
                light_map_coord: Coord = view_coord.add(light_emitter_coord.scale(-1))
                distance = int(abs((light_map_coord.x ** 2) + (light_map_coord.y ** 2)) ** 0.5)
                if distance <= radius:
                    light_map.light(light_map_coord)
            self.light_map_registry.register_light_map(radius, light_map)
            print(f"[lighting] Built LightMap for radius {radius} with {len(light_map)} lit tiles.")
            if len(light_map) == max_lit_tiles:
                print(f"[lighting] Maximum lit tiles of {max_lit_tiles} reached at radius {radius}, terminating light map generation.")
                break
        print(f"[lighting] Registered {len(self.light_map_registry.light_maps)} light maps.")

class LevelLightMapBaker:

    FIXED_LIGHT_RADIUS = 3

    # Injectable
    display_config: DisplayConfig
    light_map_registry: LightMapRegistry
    u5_map_registry: U5MapRegistry
    terrain_registry: TerrainRegistry

    # all baked level light maps are built in coords relative to the level map
    def bake_level_light_maps(self):

        default_light_map = self.light_map_registry.get_light_map(__class__.FIXED_LIGHT_RADIUS)

        for location_index, u5_map in self.u5_map_registry.u5maps.items():
            num_location_lights = 0
            for level_index in u5_map.levels.keys():
                level_light_map = LightMap()
                for light_emitter_coord in u5_map.get_coord_iteration():
                    tile_id = u5_map.get_tile_id(level_index, light_emitter_coord)
                    terrain = self.terrain_registry.get_terrain(tile_id)
                    if terrain.emits_light:
                        default_light_map.bake_level_light_map(level_light_map, light_emitter_coord)
                self.light_map_registry.register_baked_light_map(location_index, level_index, level_light_map)
            print(f"[lighting] Baked {num_location_lights} fixed lights for {u5_map.location_metadata.name} (location_index={location_index})")
