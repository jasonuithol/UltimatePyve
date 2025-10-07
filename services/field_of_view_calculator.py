from dark_libraries.dark_math import Coord, Rect

from services.map_cache.map_cache_service import MapCacheService

class FieldOfViewCalculator:

    map_cache_service: MapCacheService

    def calculate_fov_visibility(
        self, 
        location_index: int,
        level_index: int,
        fov_centre_coord: Coord, # must be in world co-ordinates.
        view_rect: Rect          # must be in world co-ordinates.
    ) -> set[Coord]:

        # these are the coords you can be on to make windows transparent to light.
        windowed_coords = fov_centre_coord.get_4way_neighbours()

        # I'm pretty sure set.copy() is broken af.
        queued:  set[Coord] = {fov_centre_coord}
        visited: set[Coord] = {fov_centre_coord}
        result:  set[Coord] = set()

        while len(queued):
            world_coord = queued.pop()

            result.add(world_coord)

            coord_contents = self.map_cache_service.get_coord_contents(location_index, level_index, world_coord)
            terrain = coord_contents.get_terrain()

            allows_light = not terrain.blocks_light or (world_coord in windowed_coords and terrain.windowed)

            if allows_light or world_coord == fov_centre_coord:
                for neighbour_coord in world_coord.get_8way_neighbours():
                    if view_rect.is_in_bounds(neighbour_coord) and not neighbour_coord in visited:

                        # this square is in view, and has a neighbour that is visible, and doesn't block light.
                        queued.add(neighbour_coord)

                        # this is an infinite loop unless we track this.
                        visited.add(neighbour_coord)
        return result