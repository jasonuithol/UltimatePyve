from pathlib import Path
from navigation.u5map import U5Map
from dark_libraries.dark_math import Size

from loaders.tileset import load_tiles16_raw, ega_palette, TILES16_PATH
from loaders.data import DataOVL

# === CONFIG ===
BRIT_DAT_PATH = r".\u5\BRIT.DAT"

# === CONSTANTS ===
GRID_DIM    = 16
CHUNK_DIM   = 16
MAP_DIM     = GRID_DIM * CHUNK_DIM
HEADER_OFF  = 0x3886
HEADER_LEN  = GRID_DIM * GRID_DIM
VOID_MARKER = 0xFF

_map: U5Map = None

def load_britannia() -> U5Map:
    global _map
    if _map is None:
        ovl = DataOVL.load()
        chunk_map = list(ovl.britannia_chunking_info)
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
        _map = U5Map("BRITANNIA", Size(MAP_DIM, MAP_DIM), tileset, ega_palette, [tiles], CHUNK_DIM, GRID_DIM, None)
    return _map

if __name__ == "__main__":
    from loaders.location import render_location_map_to_disk
    britannia = load_britannia()
    surf = render_location_map_to_disk(britannia, 0)
