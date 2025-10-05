from dark_libraries.dark_math import Coord

from game.player_state import PlayerState
from game.world_clock import WorldClock

from .light_map import LightMap
from .light_map_registry import LightMapRegistry

class LightingCalculator:

    # Injectable
    world_clock: WorldClock
    light_map_registry: LightMapRegistry
    player_state: PlayerState

    def get_player_light_radius(self):
        current_radius = self.world_clock.get_current_light_radius()

        # in case the player has lit a torch or something
        if not self.player_state.light_radius is None:
            current_radius = max(current_radius, self.player_state.light_radius)
            
        viewable_radius = max(1, min(current_radius, self.light_map_registry.get_maximum_radius()))

        return viewable_radius


    def calculate_lighting(self, location_index: int, level_index: int, player_light_radius: int, player_coord: Coord, fov_visible_coords: set[Coord]) -> set[Coord]:

        player_light_radius = self.get_player_light_radius()

        baked_player_light_map: LightMap = self.light_map_registry.get_light_map(player_light_radius).translate(player_coord).intersect(fov_visible_coords)
        baked_level_light_maps = self.light_map_registry.get_baked_light_maps(location_index, level_index)

        # Make a set of lit coords in the view_rect
        lit_world_coords: set[Coord] = set(baked_player_light_map.coords.keys())
        if not baked_level_light_maps is None:
            for light_emitter_coord, baked_level_light_map in baked_level_light_maps.items():

                if light_emitter_coord in fov_visible_coords:
                    lit_world_coords.update(baked_level_light_map.coords.keys())

        return lit_world_coords