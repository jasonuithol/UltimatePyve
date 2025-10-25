import math

from dark_libraries.dark_math import Vector2

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.light_map import LightMap
from view.display_config import DisplayConfig

class LightMapBuilder(LoggerMixin):

    # Injectable
    display_config: DisplayConfig
    global_registry: GlobalRegistry
    
    # Builds an unbaked lightmap of specified radius
    def _build_light_map(self, radius: int, light_emitter_view_offset: Vector2[int]) -> LightMap:
        light_map_centre = 0,0
        light_map = LightMap()
        for view_coord in self.display_config.VIEW_PORT_SIZE.__iter__():
            light_map_offset: Vector2[int] = view_coord.to_offset() - light_emitter_view_offset

            # This tweak makes the lightmaps the right shape
            biblically_accurate_radius_offset = 0.5

            distance = int(light_map_offset.pythagorean_distance(light_map_centre) + biblically_accurate_radius_offset)
            if distance <= radius:
                light_map.light(light_map_offset)
        return light_map

    # all unbaked light maps are built in coords relative to the light emitter.
    def build_light_maps(self):

        light_emitter_view_offset = Vector2[int](self.display_config.VIEW_PORT_SIZE.w // 2, self.display_config.VIEW_PORT_SIZE.h // 2)

        max_dimension_size = max(self.display_config.VIEW_PORT_SIZE.w, self.display_config.VIEW_PORT_SIZE.h)
        max_lit_tiles = self.display_config.VIEW_PORT_SIZE.w * self.display_config.VIEW_PORT_SIZE.h

        # We need to draw radii right up to the corners, extending beyond the viewport in the extreme cases.
        # so calculate the max radius using the tile diagonals, not the tile horiz/vert sizes.
        max_radius = math.ceil(max_dimension_size * (2 ** 0.5))

        for radius in range(1, max_radius + 1):

            light_map = self._build_light_map(radius, light_emitter_view_offset)
            self.global_registry.unbaked_light_maps.register(radius, light_map)
            self.log(f"DEBUG: Built LightMap for radius {radius} with {len(light_map)} lit tiles.")

            # We are building too many radii, so let's just cut it off when we've lit every viewable tile, 
            # rather than tune the math that needs to be tuned for shape, not limits.
            if len(light_map) == max_lit_tiles:
                self.log(f"Maximum lit tiles of {max_lit_tiles} reached at radius {radius}, terminating light map generation.")
                break

        self.log(f"Registered {len(self.global_registry.unbaked_light_maps)} light maps.")