# file: maps/overworld.py
from pathlib import Path

from dark_libraries.dark_math import Size

from .u5map import U5Map
from .data import DataOVL

# === CONFIG ===
BRIT_DAT_PATH = r".\u5\BRIT.DAT"

# === CONSTANTS ===
GRID_DIM    = 16
CHUNK_DIM   = 16
MAP_DIM     = GRID_DIM * CHUNK_DIM
HEADER_OFF  = 0x3886
HEADER_LEN  = GRID_DIM * GRID_DIM
VOID_MARKER = 0xFF

class Britannia(U5Map):
    pass

def load_britannia() -> Britannia:
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
    return Britannia("BRITANNIA", Size(MAP_DIM, MAP_DIM), [tiles], CHUNK_DIM, GRID_DIM, None)

if __name__ == "__main__":
    u5map: U5Map = load_britannia()
    u5map.render_to_disk(0)
