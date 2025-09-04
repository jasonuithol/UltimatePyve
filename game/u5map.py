# file: u5map.py
from typing import List, Optional
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord, Size
from loaders.tileset import TileSet

@auto_init
@immutable
class LocationMetadata:
    name: str                   # name of the location
    name_index: int             # which name the location takes.
    files_index: int            # which file the location is in
    group_index: int            # order of appearance of the town in the file. Use for indexing into DATA.OVL properties.
    map_index_offset: int       # how many levels to skip to start reading the first level of the location.
    num_levels: int             # how many levels the location contains
    default_level: int          # which level the player spawns in when entering the location.
    trigger_index: int          # the index the entry triggers for this location are at.

@auto_init
@immutable
class U5Map:
    name: str
    size_in_tiles: Size
    tileset: TileSet                      # tile pixel data and metadata
    levels: List[bytearray]               # width*height tile IDs per level
    chunk_dim: int                        # 16 for U5
    grid_dim: int                         # size_in_tiles.w/chunk_dim
    location_metadata: Optional[LocationMetadata]   # if this is a sub-location of the world e.g. a town, keep, dwelling, castle.

    def is_in_bounds(self, x: int, y: int) -> bool:
        return Coord(x,y).is_in_bounds(self.size_in_tiles)

    def get_wrapped_coord(self, coord: Coord) -> Coord:
        return Coord(coord.x % self.size_in_tiles.x, coord.y % self.size_in_tiles.y)

    def get_tile_id(self, level_ix: int, x: int, y: int) -> int:

        assert self.is_in_bounds(x, y), f"Coordinates {x}, {y} out of bounds."

        try:
            level = self.levels[level_ix]
        except Exception as e:
            print(f"Error accessing level {level_ix} from levels list, size {len(self.levels)}: {e}")
            raise

        try:
            index = y * self.size_in_tiles.w + x
            return level[index]
        except Exception as e:
            print(f"Error accessing tile {index} from level, size {len(level)}: {e}")
            raise
