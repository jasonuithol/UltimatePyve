import math
from typing import Self

from dark_libraries.dark_math import Coord, Rect

from game.terrain.terrain_registry import TerrainRegistry
from maps.u5map import U5Map
from maps.u5map_registry import U5MapRegistry

from .display_config import DisplayConfig
from .field_of_view import FieldOfViewCalculator
from .queried_tiles import QueriedTileGenerator

class LightMap:

    def __init__(self):
        self.coords: dict[Coord, int] = {}

    def __str__(self):
        return f"LightMap=" + list(self.coords.keys()).__str__()
    
    def __repr__(self):
        return f"LightMap=" + list(self.coords.keys()).__str__()

    def __iter__(self):
        return self.coords.__iter__()

    def __len__(self):
        return self.coords.__len__()

    def copy(self) -> Self:
        clone = self.__class__()
        clone.coords = self.coords.copy()
        return clone

    def is_lit(self, coord: Coord) -> bool:
        return coord in self.coords.keys()

    def light(self, coord: Coord):
        # will silently ignore duplicate coords, which is perfect.
        self.coords[coord] = 1

    def bake_level_light_map(self, level_light_map: Self, light_emitter_level_coord: Coord, visible_world_coords: set[Coord] | None):

        assert len(self) > 0, "Cannot bake with an empty light map."
        assert len(self) > 0, "Cannot bake an empty level map."
        assert visible_world_coords is None or len(visible_world_coords) > 0, "Empty visible world coords is impossible."

        for light_coord in self:
            level_light_map_coord = light_emitter_level_coord.add(light_coord)
            if visible_world_coords is None or level_light_map_coord in visible_world_coords:
                # view_port_coord starts at 0,0 relative to the view_port.
                # light_emitter_coord is relative to the level map coords.
                level_light_map.light(level_light_map_coord)

class LightMapRegistry:
    def _after_inject(self):
        self.maximum_radius = 0
        self.light_maps: dict[int, LightMap] = {}
        self.baked_light_maps: dict[tuple[int, int], LightMap] = {}
    
    def register_light_map(self, radius: int, light_map: LightMap):
        assert len(light_map) > 0, "Probably DON'T want to register an empty light map ?"
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
    
    # Builds an unbaked lightmap of specified radius
    def _build_light_map(self, radius: int) -> LightMap:
        light_map = LightMap()
        for view_coord in self.display_config.VIEW_PORT_SIZE:
            light_map_coord: Coord = view_coord.add(self.light_emitter_coord.scale(-1))
            distance = int(abs((light_map_coord.x ** 2) + (light_map_coord.y ** 2)) ** 0.5)
            if distance <= radius:
                light_map.light(light_map_coord)
        return light_map

    # all unbaked light maps are built in coords relative to the light emitter.
    def build_light_maps(self):

        self.light_emitter_coord = Coord(self.display_config.VIEW_PORT_SIZE.w // 2, self.display_config.VIEW_PORT_SIZE.h // 2)

        max_dimension_size = max(self.display_config.VIEW_PORT_SIZE.w, self.display_config.VIEW_PORT_SIZE.h)
        max_lit_tiles = self.display_config.VIEW_PORT_SIZE.w * self.display_config.VIEW_PORT_SIZE.h

        # We need to draw radii right up to the corners, extending beyond the viewport in the extreme cases.
        # so calculate the max radius using the tile diagonals, not the tile horiz/vert sizes.
        max_radius = math.ceil(max_dimension_size * (2 ** 0.5))

        for radius in range(1, max_radius + 1):

            light_map = self._build_light_map(radius)
            self.light_map_registry.register_light_map(radius, light_map)
            print(f"[lighting] Built LightMap for radius {radius} with {len(light_map)} lit tiles.")

            # We are building too many radii, so let's just cut it off when we've lit every viewable tile, 
            # rather than tune the math that needs to be tuned for shape, not limits.
            if len(light_map) == max_lit_tiles:
                print(f"[lighting] Maximum lit tiles of {max_lit_tiles} reached at radius {radius}, terminating light map generation.")
                break

        print(f"[lighting] Registered {len(self.light_map_registry.light_maps)} light maps.")

class LevelLightMapBaker:

    FIXED_LIGHT_RADIUS = 3

    # Injectable
    display_config:         DisplayConfig
    light_map_registry:     LightMapRegistry
    u5_map_registry:        U5MapRegistry
    terrain_registry:       TerrainRegistry
    fov_calculator:         FieldOfViewCalculator
    queried_tile_generator: QueriedTileGenerator

    def _bake_level(self, u5_map: U5Map, level_index: int) -> int:

        level_light_map = LightMap()
        num_lights = 0

        for light_emitter_coord in u5_map.get_coord_iteration():
            tile_id = u5_map.get_tile_id(level_index, light_emitter_coord)
            terrain = self.terrain_registry.get_terrain(tile_id)
            if terrain.emits_light:

                # Calculate which tiles are visible from the light emitter's field of view.
                view_rect = Rect(
                    light_emitter_coord.add(Coord(-1 * __class__.FIXED_LIGHT_RADIUS, -1 * __class__.FIXED_LIGHT_RADIUS)), 
                    size = (
                        2 * __class__.FIXED_LIGHT_RADIUS + 1,
                        2 * __class__.FIXED_LIGHT_RADIUS + 1
                    )
                )
                queried_tiles = self.queried_tile_generator.query_tile_grid(u5_map, level_index, view_rect, skip_interactables = True)
                visible_tiles = self.fov_calculator.calculate_fov_visibility(queried_tiles, light_emitter_coord, view_rect)
                visible_world_coords = {coord for coord in visible_tiles.keys()}

                self.default_light_map.bake_level_light_map(level_light_map, light_emitter_coord, visible_world_coords)
                num_lights += 1

        self.light_map_registry.register_baked_light_map(
            u5_map.location_metadata.location_index, 
            level_index, 
            level_light_map
        )

        return num_lights
    
    # all baked level light maps are built in coords relative to the level map
    def bake_level_light_maps(self):

        self.default_light_map = self.light_map_registry.get_light_map(__class__.FIXED_LIGHT_RADIUS)

        for location_index, u5_map in self.u5_map_registry.u5maps.items():
            num_lights = 0

            for level_index in u5_map.levels.keys():

                print(f"Baking light levels for {u5_map.location_metadata.name}, level={level_index}")
                num_lights += self._bake_level(u5_map, level_index)

            print(f"[lighting] Baked {num_lights} fixed lights for {u5_map.location_metadata.name} (location_index={location_index})")
