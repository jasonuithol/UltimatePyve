from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame

from tileset import TILE_SIZE

@dataclass
class U5Map:
    name: str
    width: int
    height: int
    tileset: List[pygame.Surface]         # indexed tile graphics
    palette: List[Tuple[int, int, int]]   # EGA palette
    levels: List[bytearray]               # a list of levels consisting of width*height tile indices
    chunk_dim: int                        # 16 for U5
    grid_dim: int                         # width/chunk_dim

    def get_tile_id(self, level_ix: int, x: int, y: int) -> int:
        try:
            level = self.levels[level_ix]
        except Exception as e:
            print(f"Error accessing level {level_ix} from levels list, size {len(self.levels)}: {e}")
            raise e
        
        try:
            index = y * self.width + x
            return level[index]
        except Exception as e:
            print(f"Error accessing tile {index} from level, size {len(level)}: {e}")
            raise e

    def render(
        self,
        level_ix: int = 0,
        tile_size: int = TILE_SIZE,
        rect: Optional[Tuple[int, int, int, int]] = None,
    ) -> pygame.Surface:
        """
        Render the map or a subsection of it.

        rect: (tile_x, tile_y, tile_w, tile_h) in tile coordinates.
              If None, renders the whole map.
        """
        if rect is None:
            rect = (0, 0, self.width, self.height)

        tx, ty, tw, th = rect
        surf = pygame.Surface((tw * tile_size, th * tile_size))

        for y in range(th):
            for x in range(tw):
                map_x = tx + x
                map_y = ty + y
                if 0 <= map_x < self.width and 0 <= map_y < self.height:
                    tid = self.get_tile_id(level_ix, map_x, map_y)
                    if 0 <= tid < len(self.tileset):
                        surf.blit(self.tileset[tid], (x * tile_size, y * tile_size))
        return surf