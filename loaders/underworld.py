# file: underworld.py

from pathlib import Path
from u5map import U5Map
from loaders.tileset import load_tiles16_raw, ega_palette, TILES16_PATH
from dark_math import Size

# === CONFIG ===
UNDER_DAT_PATH = r".\u5\UNDER.DAT"

# === CONSTANTS ===
GRID_DIM   = 16       # 16×16 chunks
CHUNK_DIM  = 16       # 16×16 tiles per chunk
MAP_DIM    = GRID_DIM * CHUNK_DIM  # 256×256 tiles

_map: U5Map = None

# --- Load UNDER.DAT directly ---
def load_underworld() -> U5Map:
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
        tileset = load_tiles16_raw(TILES16_PATH)
        _map = U5Map("UNDERWORLD", Size(MAP_DIM, MAP_DIM), tileset, ega_palette, [tiles], CHUNK_DIM, GRID_DIM, None)
    return _map

if __name__ == "__main__":
    from loaders.location import render_location_map_to_disk
    underworld = load_underworld()
    surf = render_location_map_to_disk(underworld, 0)

