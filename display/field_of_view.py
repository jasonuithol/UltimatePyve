from dark_libraries.dark_math import Coord, Rect
from .queried_tiles import QueriedTile

class FieldOfViewCalculator:

    def calculate_fov_visibility(
        self, 
        queried_tile_grid_dict: dict[Coord, QueriedTile], 
        fov_centre_coord: Coord, # must be in world co-ordinates
        view_rect: Rect          # must be in world co-ordinates
    ) -> dict[Coord, QueriedTile]:

        # these are the coords you can be on to make windows transparent to light.
        windowed_coords = fov_centre_coord.get_4way_neighbours()

        # I'm pretty sure set.copy() is broken af.
        queued:  set[Coord] = {fov_centre_coord}
        visited: set[Coord] = {fov_centre_coord}
        result:  dict[Coord, QueriedTile] = {}

        while len(queued):
            world_coord = queued.pop()
            queried_tile = queried_tile_grid_dict[world_coord]

            result[world_coord] = queried_tile

            allows_light = queried_tile.terrain == None or not queried_tile.terrain.blocks_light or (world_coord in windowed_coords and queried_tile.terrain.windowed)

            if allows_light or world_coord == fov_centre_coord:
                for neighbour_coord in world_coord.get_8way_neighbours():
                    if view_rect.is_in_bounds(neighbour_coord) and not neighbour_coord in visited:

                        # this square is in view, and has a neighbour that is visible, and doesn't block light.
                        queued.add(neighbour_coord)

                        # this is an infinite loop unless we track this.
                        visited.add(neighbour_coord)
        return result