from dark_libraries.dark_math import Coord, Rect, Vector2

from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.terrain         import Terrain
from models.u5_map          import U5Map
from models.light_map       import LightMap

from services.field_of_view_calculator import FieldOfViewCalculator
from view.display_config import DisplayConfig

class LightMapLevelBaker:

    FIXED_LIGHT_RADIUS = 3

    # Injectable
    display_config:     DisplayConfig
    global_registry:    GlobalRegistry
    fov_calculator:     FieldOfViewCalculator

    def _get_fov_visible_coords(self, location_index: int, level_index: int, light_emitter_coord: Coord) -> set[Coord]:

        radius_offset = Vector2(__class__.FIXED_LIGHT_RADIUS, __class__.FIXED_LIGHT_RADIUS)
        centre_thiccness = (1,1)

        # Calculate which tiles are visible from the light emitter's field of view.
        view_rect = Rect(
            light_emitter_coord - radius_offset, 
            size = (radius_offset * 2) + centre_thiccness
        )
        return self.fov_calculator.calculate_fov_visibility(location_index, level_index, light_emitter_coord, view_rect)

    def _bake_light_map(self, location_index: int, level_index: int, light_emitter_coord: Coord):

        visible_world_coords = self._get_fov_visible_coords(location_index, level_index, light_emitter_coord)
        baked_light_map = self.default_light_map.translate(light_emitter_coord).intersect(visible_world_coords)

        light_emitter_location = GlobalLocation(
            location_index, 
            level_index, 
            light_emitter_coord
        )

        self.global_registry.baked_light_maps.register(
            light_emitter_location,
            baked_light_map
        )

    def _bake_level(self, u5_map: U5Map, level_index: int) -> int:
        num_lights = 0
        for map_coord in u5_map.get_coord_iteration():
            tile_id = u5_map.get_tile_id(level_index, map_coord)
            terrain: Terrain = self.global_registry.terrains.get(tile_id)
            if terrain.emits_light:
                self._bake_light_map(
                    u5_map.location_metadata.location_index, 
                    level_index, 
                    light_emitter_coord = map_coord
                )
                num_lights += 1
        return num_lights
    
    # all baked level light maps are built in coords relative to the level map
    def bake_level_light_maps(self):

        self.default_light_map: LightMap = self.global_registry.unbaked_light_maps.get(__class__.FIXED_LIGHT_RADIUS)

        for location_index, u5_map in self.global_registry.maps.items():
            num_lights = 0
            for level_index in u5_map.levels.keys():
                num_lights += self._bake_level(u5_map, level_index)

            print(f"[lighting] Baked {num_lights} fixed lights for {u5_map.location_metadata.name} (location_index={location_index})")