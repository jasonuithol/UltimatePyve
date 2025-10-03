import math
from typing import Self

from dark_libraries.dark_math import Coord, Rect, Vector2

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

    def translate(self, centre_offset: Coord):
        translated = LightMap()
        for coord in self.coords.keys():
            translated.coords[centre_offset + coord] = 1
        return translated

    def intersect(self, coords: set[Coord]):
        intersected = LightMap()
        for coord in self.coords.keys():
            if coord in coords:
                intersected.coords[coord] = 1
        return intersected

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

class LightMapBuilder:

    # Injectable
    display_config: DisplayConfig
    light_map_registry: LightMapRegistry
    
    # Builds an unbaked lightmap of specified radius
    def _build_light_map(self, radius: int) -> LightMap:
        light_map_centre = 0,0
        light_map = LightMap()
        for view_coord in self.display_config.VIEW_PORT_SIZE:
            light_map_coord: Coord = view_coord - self.light_emitter_coord

            # This tweak makes the lightmaps the right shape
            biblically_accurate_offset = 0.5

            distance = int(light_map_coord.pythagorean_distance(light_map_centre) + biblically_accurate_offset)
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

    def _get_fov_visible_coords(self, u5_map: U5Map, level_index: int, light_emitter_coord: Coord) -> set[Coord]:

        radius_offset = Vector2(__class__.FIXED_LIGHT_RADIUS, __class__.FIXED_LIGHT_RADIUS)
        centre_thiccness = (1,1)

        # Calculate which tiles are visible from the light emitter's field of view.
        view_rect = Rect(
            light_emitter_coord - radius_offset, 
            size = (radius_offset * 2) + centre_thiccness
        )
        queried_tiles = self.queried_tile_generator.query_tile_grid(u5_map, level_index, view_rect, skip_interactables = True)
        visible_tiles = self.fov_calculator.calculate_fov_visibility(queried_tiles, light_emitter_coord, view_rect)
        visible_world_coords = {coord for coord in visible_tiles.keys()}
        return visible_world_coords

    def _bake_light_map(self, u5_map: U5Map, level_index: int, light_emitter_coord: Coord):

        visible_world_coords = self._get_fov_visible_coords(u5_map, level_index, light_emitter_coord)
        baked_light_map = self.default_light_map.translate(light_emitter_coord).intersect(visible_world_coords)

        self.light_map_registry.register_baked_light_map(
            u5_map.location_metadata.location_index, 
            level_index, 
            light_emitter_coord,
            baked_light_map
        )

    def _bake_level(self, u5_map: U5Map, level_index: int) -> int:
        num_lights = 0
        for light_emitter_coord in u5_map.get_coord_iteration():
            tile_id = u5_map.get_tile_id(level_index, light_emitter_coord)
            terrain = self.terrain_registry.get_terrain(tile_id)
            if terrain.emits_light:
                self._bake_light_map(u5_map, level_index, light_emitter_coord)
                num_lights += 1
        return num_lights
    
    # all baked level light maps are built in coords relative to the level map
    def bake_level_light_maps(self):

        self.default_light_map = self.light_map_registry.get_light_map(__class__.FIXED_LIGHT_RADIUS)

        for location_index, u5_map in self.u5_map_registry.u5maps.items():
            num_lights = 0
            for level_index in u5_map.levels.keys():
                num_lights += self._bake_level(u5_map, level_index)

            print(f"[lighting] Baked {num_lights} fixed lights for {u5_map.location_metadata.name} (location_index={location_index})")
