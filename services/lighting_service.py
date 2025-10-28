from dark_libraries.dark_math import Coord

from data.global_registry import GlobalRegistry
from models.global_location import GlobalLocation
from models.agents.party_agent import PartyAgent
from services.light_map_level_baker import LightMapLevelBaker
from services.world_clock import WorldClock

from models.light_map import LightMap

class LightingService:

    # Injectable
    world_clock: WorldClock
    party_state: PartyAgent
    global_registry: GlobalRegistry
    light_map_level_baker: LightMapLevelBaker

    def init(self):
        # Needs FOV calculator, which needs map_cache.
        self.light_map_level_baker.bake_level_light_maps()

    def get_player_light_radius(self):
        current_radius = self.world_clock.get_current_light_radius()

        # in case the player has lit a torch or something
        if not self.party_state.light_radius is None:
            current_radius = max(current_radius, self.party_state.light_radius)
            
        viewable_radius = max(1, min(current_radius, max(self.global_registry.unbaked_light_maps.keys())))

        return viewable_radius


    def calculate_lighting(self, fov_centre_location: GlobalLocation, player_light_radius: int, fov_visible_coords: set[Coord[int]]) -> set[Coord[int]]:

        #
        # TODO: Since this service already accesses party_state, do we actually need to pass in party_location ?  
        # ANSWER: No not really, but we currently need to pass it into FovCalculator, so we do it anyway.
        #

#        player_light_radius = self.get_player_light_radius()

        baked_player_light_map: LightMap = self.global_registry.unbaked_light_maps.get(player_light_radius).translate(fov_centre_location.coord).intersect(fov_visible_coords)
        baked_level_light_maps = self.global_registry.baked_light_level_maps.get((fov_centre_location.location_index, fov_centre_location.level_index))

        # Make a set of lit coords in the view_rect
        lit_world_coords: set[Coord[int]] = set(baked_player_light_map.coords_or_offsets.keys())
        if not baked_level_light_maps is None:
            for light_emitter_coord, baked_level_light_map in baked_level_light_maps.items():

                if light_emitter_coord in fov_visible_coords:
                    lit_world_coords.update(baked_level_light_map.coords_or_offsets.keys())

        return lit_world_coords