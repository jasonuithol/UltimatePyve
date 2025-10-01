from dark_libraries.dark_math import Coord, Rect, Vector2
from .queried_tiles import QueriedTile

WINDOWED_VECTORS = [
    Vector2( 0,  1), # bottom
    Vector2( 0, -1), # top
    Vector2( 1,  0), # right
    Vector2(-1,  0), # left
]

NEIGHBOUR_VECTORS = WINDOWED_VECTORS + [
    Vector2( 1,  1), # bottom-right
    Vector2( 1, -1), # top-right
    Vector2(-1,  1), # bottom-left
    Vector2(-1, -1)  # bottom-right
]

class FieldOfViewCalculator:

    def calculate_fov_visibility(
        self, 
        queried_tile_grid_dict: dict[Coord, QueriedTile], 
        fov_centre_coord: Coord, # must be in world co-ordinates
        view_rect: Rect          # must be in world co-ordinates
    ) -> dict[Coord, QueriedTile]:

        # these are the coords you can be on to make windows transparent to light.
        windowed_coords = [fov_centre_coord.add(windowed_vector) for windowed_vector in WINDOWED_VECTORS]

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
                for neighbour_vector in NEIGHBOUR_VECTORS:
                    neighbour_coord = world_coord.add(neighbour_vector)
                    if view_rect.is_in_bounds(neighbour_coord) and not neighbour_coord in visited:

                        # this square is in view, and has a neighbour that is visible, and doesn't block light.
                        queued.add(neighbour_coord)

                        # this is an infinite loop unless we track this.
                        visited.add(neighbour_coord)
        return result