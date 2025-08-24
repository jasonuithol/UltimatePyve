# file: u5_loader.py

import pygame
from pathlib import Path

# === CONFIG ===
DATA_OVL_PATH = r".\u5\DATA.OVL"
BRIT_DAT_PATH = r".\u5\BRIT.DAT"
BRIT_OOL_PATH = r".\u5\BRIT.OOL"
TILE_SIZE     = 2  # pixels per tile in output images

# === CONSTANTS ===
GRID_DIM    = 16
CHUNK_DIM   = 16
MAP_DIM     = GRID_DIM * CHUNK_DIM
HEADER_OFF  = 0x3886
HEADER_LEN  = GRID_DIM * GRID_DIM  # 256 bytes
VOID_MARKER = 0xFF

def load_pc_brit_map(data_ovl_path, brit_dat_path, brit_ool_path):
    # Read chunk map from DATA.OVL
    ovl = Path(data_ovl_path).read_bytes()
    chunk_map = list(ovl[HEADER_OFF:HEADER_OFF+HEADER_LEN])
    if len(chunk_map) != HEADER_LEN:
        raise ValueError("Chunk map not found or wrong length")

    # Read all-water chunk
    ool = Path(brit_ool_path).read_bytes()
    if len(ool) != CHUNK_DIM * CHUNK_DIM:
        raise ValueError("BRIT.OOL wrong size")

    # Read non-water chunks
    chunks_data = Path(brit_dat_path).read_bytes()
    if len(chunks_data) % (CHUNK_DIM * CHUNK_DIM) != 0:
        raise ValueError("BRIT.DAT size not multiple of chunk size")
    chunk_list = [
        chunks_data[i*CHUNK_DIM*CHUNK_DIM:(i+1)*CHUNK_DIM*CHUNK_DIM]
        for i in range(len(chunks_data) // (CHUNK_DIM * CHUNK_DIM))
    ]

    # Expand to full map
    tiles = bytearray(MAP_DIM * MAP_DIM)
    chunk_id_map = [[None]*GRID_DIM for _ in range(GRID_DIM)]
    for gy in range(GRID_DIM):
        for gx in range(GRID_DIM):
            cid = chunk_map[gy*GRID_DIM + gx]
            chunk_id_map[gy][gx] = cid
            if cid == VOID_MARKER or cid >= len(chunk_list):
                chunk = ool
            else:
                chunk = chunk_list[cid]
            for cy in range(CHUNK_DIM):
                dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                src = cy * CHUNK_DIM
                tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]
    return tiles, chunk_id_map

def render_by_tile_id(tiles, tile_size, out_file):
    pygame.init()
    surf = pygame.Surface((MAP_DIM*tile_size, MAP_DIM*tile_size))
    for y in range(MAP_DIM):
        for x in range(MAP_DIM):
            tid = tiles[y*MAP_DIM + x]
            # crude palette: water blue, else pseudo-random colour
            colour = (0, 96, 192) if tid == 0x01 else ((tid*5)%256, (tid*11)%256, (tid*17)%256)
            pygame.draw.rect(surf, colour, (x*tile_size, y*tile_size, tile_size, tile_size))
    pygame.image.save(surf, out_file)
    print(f"Saved {out_file}")

def render_by_chunk_id(chunk_id_map, tile_size, out_file):
    pygame.init()
    surf = pygame.Surface((MAP_DIM*tile_size, MAP_DIM*tile_size))
    for gy in range(GRID_DIM):
        for gx in range(GRID_DIM):
            cid = chunk_id_map[gy][gx]
            # void chunks get black, others get colour from ID
            if cid == VOID_MARKER:
                colour = (0, 0, 0)
            else:
                colour = ((cid*40) % 256, (cid*85) % 256, (cid*170) % 256)
            for cy in range(CHUNK_DIM):
                for cx in range(CHUNK_DIM):
                    x = gx*CHUNK_DIM + cx
                    y = gy*CHUNK_DIM + cy
                    pygame.draw.rect(surf, colour, (x*tile_size, y*tile_size, tile_size, tile_size))
    pygame.image.save(surf, out_file)
    print(f"Saved {out_file}")

if __name__ == "__main__":
    tiles, chunk_id_map = load_pc_brit_map(DATA_OVL_PATH, BRIT_DAT_PATH, BRIT_OOL_PATH)
    render_by_tile_id(tiles, TILE_SIZE, "britannia_tiles.png")
    render_by_chunk_id(chunk_id_map, TILE_SIZE, "britannia_chunks.png")