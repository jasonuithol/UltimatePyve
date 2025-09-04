# file: underworld.py

from pathlib import Path
from game.u5map import U5Map
from loaders.tileset import load_tileset
from dark_libraries.dark_math import Size

# === CONFIG ===
UNDER_DAT_PATH = r".\u5\UNDER.DAT"

# === CONSTANTS ===
GRID_DIM   = 16       # 16×16 chunks
CHUNK_DIM  = 16       # 16×16 tiles per chunk
MAP_DIM    = GRID_DIM * CHUNK_DIM  # 256×256 tiles

class UnderWorld(U5Map):
    pass

_map: UnderWorld = None

# --- Load UNDER.DAT directly ---
def load_underworld() -> UnderWorld:
    global _map
    if _map is None:
        raw = Path(UNDER_DAT_PATH).read_bytes()
        # UNDER.DAT is exactly 256 chunks × 256 bytes each
        chunks = [raw[i*256:(i+1)*256] for i in range(len(raw)//256)]
        tiles = bytearray(MAP_DIM * MAP_DIM)
        for gy in range(GRID_DIM):
            for gx in range(GRID_DIM):
                chunk = chunks[gy*GRID_DIM + gx]
                for cy in range(CHUNK_DIM):
                    dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                    src = cy * CHUNK_DIM
                    tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]
        tileset = load_tileset()
        _map = UnderWorld("UNDERWORLD", Size(MAP_DIM, MAP_DIM), tileset, [tiles], CHUNK_DIM, GRID_DIM, None)
    return _map

if __name__ == "__main__":
    from loaders.location import render_location_map_to_disk
    underworld = load_underworld()
    surf = render_location_map_to_disk(underworld, 0)

