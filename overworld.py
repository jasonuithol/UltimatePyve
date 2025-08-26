from pathlib import Path
from u5map import U5Map
from tileset import load_tiles16_raw, ega_palette, TILES16_PATH
from data import DataOVL

# === CONFIG ===
BRIT_DAT_PATH = r".\u5\BRIT.DAT"

# === CONSTANTS ===
GRID_DIM    = 16
CHUNK_DIM   = 16
MAP_DIM     = GRID_DIM * CHUNK_DIM
HEADER_OFF  = 0x3886
HEADER_LEN  = GRID_DIM * GRID_DIM
VOID_MARKER = 0xFF

def load_britannia() -> U5Map:

    ovl = DataOVL.load()
    chunk_map = list(ovl.britannia_chunking_info)
    '''
    ovl = Path(DATA_OVL_PATH).read_bytes()
    chunk_map = list(ovl[HEADER_OFF:HEADER_OFF+HEADER_LEN])
    '''
    chunks_data = Path(BRIT_DAT_PATH).read_bytes()
    chunk_list = [chunks_data[i*256:(i+1)*256] for i in range(len(chunks_data)//256)]
    ocean_chunk = bytes([0x01] * (CHUNK_DIM * CHUNK_DIM))
    tiles = bytearray(MAP_DIM * MAP_DIM)
    for gy in range(GRID_DIM):
        for gx in range(GRID_DIM):
            cid = chunk_map[gy*GRID_DIM + gx]
            chunk = ocean_chunk if cid == VOID_MARKER or cid >= len(chunk_list) else chunk_list[cid]
            for cy in range(CHUNK_DIM):
                dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                src = cy * CHUNK_DIM
                tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]
    tileset = load_tiles16_raw(TILES16_PATH)
    return U5Map("Britannia", MAP_DIM, MAP_DIM, tileset, ega_palette, [tiles], CHUNK_DIM, GRID_DIM)

if __name__ == "__main__":
    import pygame
    from viewer import render_map_to_surface
    OUT_FILE = "britannia_full.png"
    pygame.init()
    britannia = load_britannia()
    render_map_to_surface(britannia)
    print(f"Saved {OUT_FILE}")
    pygame.quit()
