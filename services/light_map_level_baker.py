from dark_libraries.dark_math import Coord, Rect, Vector2

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.terrain         import Terrain
from models.u5_map          import U5Map
from models.light_map       import LightMap

from services.field_of_view_calculator import FieldOfViewCalculator
from view.display_config import DisplayConfig

class LightMapLevelBaker(LoggerMixin):

    FIXED_LIGHT_RADIUS = 3

    # Injectable
    display_config:     DisplayConfig
    global_registry:    GlobalRegistry
    fov_calculator:     FieldOfViewCalculator

    def _get_fov_visible_coords(self, light_emitter_location: GlobalLocation) -> set[Coord[int]]:

        radius_offset = Vector2[int](__class__.FIXED_LIGHT_RADIUS, __class__.FIXED_LIGHT_RADIUS)
        centre_thiccness = (1,1)

        # Calculate which tiles are visible from the light emitter's field of view.
        view_rect = Rect[int](
            light_emitter_location.coord - radius_offset, 
            size = (radius_offset * 2) + centre_thiccness
        )
        return self.fov_calculator.calculate_fov_visibility(light_emitter_location, view_rect)

    def _bake_light_map(self, light_emitter_location: GlobalLocation) -> LightMap:
        visible_world_coords = self._get_fov_visible_coords(light_emitter_location)
        return self.default_light_map.translate(light_emitter_location.coord).intersect(visible_world_coords)

    def _bake_level(self, u5_map: U5Map, level_index: int) -> int:
        baked_dict = dict[Coord[int], LightMap]()
        for map_coord in u5_map.get_coord_iteration():
            tile_id = u5_map.get_tile_id(level_index, map_coord)
            terrain: Terrain = self.global_registry.terrains.get(tile_id)
            if terrain.emits_light:
                baked_dict[map_coord] = self._bake_light_map(
                    GlobalLocation(
                        u5_map.location_index, 
                        level_index, 
                        map_coord
                    )
                )
        key = (u5_map.location_index, level_index)
        self.global_registry.baked_light_level_maps.register(key, baked_dict)
        return len(baked_dict)
    
    # all baked level light maps are built in coords relative to the level map
    def bake_level_light_maps(self):

        self.default_light_map: LightMap = self.global_registry.unbaked_light_maps.get(__class__.FIXED_LIGHT_RADIUS)

        for location_index, u5_map in self.global_registry.maps.items():
            num_lights = 0
            for level_index in u5_map.get_level_indexes():
                num_lights += self._bake_level(u5_map, level_index)

            self.log(f"DEBUG: Baked {num_lights} fixed lights for {u5_map.name} (location_index={location_index})")            
        self.log(f"DEBUG: Baked {len(self.global_registry.unbaked_light_maps)} light level maps.")