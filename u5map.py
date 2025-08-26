# file: u5map.py
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class U5Map:
    name: str
    width: int
    height: int
    tileset: List[List[List[int]]]        # raw tile pixel data (palette indices)
    palette: List[Tuple[int, int, int]]   # EGA palette
    levels: List[bytearray]               # width*height tile IDs per level
    chunk_dim: int                        # 16 for U5
    grid_dim: int                         # width/chunk_dim

    def get_tile_id(self, level_ix: int, x: int, y: int) -> int:
        try:
            level = self.levels[level_ix]
        except Exception as e:
            print(f"Error accessing level {level_ix} from levels list, size {len(self.levels)}: {e}")
            raise

        try:
            index = y * self.width + x
            return level[index]
        except Exception as e:
            print(f"Error accessing tile {index} from level, size {len(level)}: {e}")
            raise
