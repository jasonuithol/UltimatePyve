# file: game/u5map.py
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord, Size

from .location_metadata import LocationMetadata

@immutable
@auto_init
class U5Map:
    size_in_tiles: Size
    levels: dict[int, bytearray]          # size_in_tiles x size_in_tiles tile IDs per level
    chunk_dim: int                        # 16 for U5
    grid_dim: int                         # size_in_tiles.w/chunk_dim
    location_metadata: LocationMetadata

    def is_in_bounds(self, coord: Coord) -> bool:
        return self.size_in_tiles.is_in_bounds(coord)

    def get_wrapped_coord(self, coord: Coord) -> Coord:
        return Coord(coord.x % self.size_in_tiles.x, coord.y % self.size_in_tiles.y)

    def get_tile_id(self, level_ix: int, coord: Coord) -> int:

        assert self.is_in_bounds(coord), f"Coordinates {coord} out of bounds."

        try:
            level = self.levels[level_ix]
        except Exception as e:
            print(f"Error accessing level {level_ix} from levels list, size {len(self.levels)}: {e}")
            raise

        try:
            index = coord.y * self.size_in_tiles.w + coord.x
            return level[index]
        except Exception as e:
            print(f"Error accessing tile {index} from level, size {len(level)}: {e}")
            raise

    def get_coord_iteration(self):
        for y in range(self.size_in_tiles.h):
            for x in range(self.size_in_tiles.w):
                yield Coord(x,y)

    def render_to_disk(self, level_index: int):
        import pygame
        from display.tileset import Tile, TileSet, load_tileset
        pygame.init()
        tile_set: TileSet = load_tileset()
        surf = pygame.Surface(self.size_in_tiles.scale(tile_set.tile_size).to_tuple())
        for x in range(self.size_in_tiles.x):
            for y in range(self.size_in_tiles.y):

                map_coord = Coord(x, y)
                tile_id = self.get_tile_id(level_index, map_coord)
                tile: Tile = tile_set.tiles[tile_id]

                pixel_coord = map_coord.scale(tile_set.tile_size)
                tile.blit_to_surface(surf, pixel_coord)
        pygame.image.save(
            surf,
            f"{self.location_metadata.name}_{level_index}.png"
        )
        pygame.quit()

        return surf