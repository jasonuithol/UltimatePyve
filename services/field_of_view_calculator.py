from dark_libraries.dark_math import Coord, Rect, Vector2

from data.global_registry import GlobalRegistry
from models.global_location import GlobalLocation
from models.terrain import Terrain
from services.map_cache.map_cache_service import MapCacheService
from services.map_cache.map_level_contents import MapLevelContents

class FieldOfViewCalculator:

    map_cache_service: MapCacheService
    global_registry:   GlobalRegistry

    def calculate_fov_visibility(
        self, 
        fov_centre_location: GlobalLocation,
        view_rect: Rect[int]          # must be in world co-ordinates.
    ) -> set[Coord[int]]:

        # these are the coords you can be on to make windows transparent to light.
        windowed_coords = fov_centre_location.coord.get_4way_neighbours()

        # I'm pretty sure set.copy() is broken af.
        queued:  set[Coord[int]] = {fov_centre_location.coord}
        visited: set[Coord[int]] = {fov_centre_location.coord}
        result:  set[Coord[int]] = set()

        map_level_contents = self.map_cache_service.get_map_level_contents(fov_centre_location.location_index, fov_centre_location.level_index)

        while len(queued):
            world_coord = queued.pop()

            result.add(world_coord)

            #
            # Calculate allows_light
            #

            interactable = self.global_registry.interactables.get(world_coord)
            if interactable is None:
                coord_contents = map_level_contents.get_coord_contents(world_coord)
                if coord_contents is None:
                    allows_light = False
                else:
                    terrain = coord_contents.get_terrain()
                    allows_light = not terrain.blocks_light or (world_coord in windowed_coords and terrain.windowed)        
            else:
                terrain = self.global_registry.terrains.get(interactable.get_current_tile_id())
                allows_light = not terrain.blocks_light or (world_coord in windowed_coords and terrain.windowed)        

            if allows_light or world_coord == fov_centre_location.coord:
                #
                # Propogate the fill algorithm
                #
                for neighbour_coord in world_coord.get_8way_neighbours():
                    if view_rect.is_in_bounds(neighbour_coord) and not neighbour_coord in visited:

                        # this square is in view, and has a neighbour that is visible, and doesn't block light.
                        queued.add(neighbour_coord)

                        # this is an infinite loop unless we track this.
                        visited.add(neighbour_coord)
        return result