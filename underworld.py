# file: underworld.py

import struct, pygame
from pathlib import Path
from u5map import U5Map
from tileset import load_tiles16, ega_palette, TILE_SIZE

# === CONFIG ===
UNDER_DAT_PATH = r".\u5\UNDER.DAT"
TILES16_PATH   = r".\u5\TILES.16"
OUT_FILE       = "underworld_full.png"

# === CONSTANTS ===
GRID_DIM   = 16       # 16×16 chunks
CHUNK_DIM  = 16       # 16×16 tiles per chunk
MAP_DIM    = GRID_DIM * CHUNK_DIM  # 256×256 tiles

# --- Load UNDER.DAT directly ---
def load_underworld() -> U5Map:
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
    tileset = load_tiles16(TILES16_PATH)
    return U5Map("Underworld", MAP_DIM, MAP_DIM, tileset, ega_palette, tiles, CHUNK_DIM, GRID_DIM)

if __name__ == "__main__":
    pygame.init()
    underworld = load_underworld()
    surf = underworld.render(TILE_SIZE)
    pygame.image.save(surf, OUT_FILE)
    print(f"Saved {OUT_FILE}")
