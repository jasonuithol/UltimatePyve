import struct, pygame
from pathlib import Path

# === CONFIG ===
DATA_OVL_PATH = r".\u5\DATA.OVL"
BRIT_DAT_PATH = r".\u5\BRIT.DAT"
BRIT_OOL_PATH = r".\u5\BRIT.OOL"
TILES16_PATH  = r".\u5\TILES.16"
OUT_FILE      = "britannia_full.png"
TILE_SIZE     = 16  # pixels per tile in tileset

# === CONSTANTS ===
GRID_DIM    = 16
CHUNK_DIM   = 16
MAP_DIM     = GRID_DIM * CHUNK_DIM
HEADER_OFF  = 0x3886
HEADER_LEN  = GRID_DIM * GRID_DIM
VOID_MARKER = 0xFF

# --- LZW decompression (12-bit codes) ---
def lzw_decompress(data):
    CLEAR, EOI = 256, 257
    code_size = 9
    dict_size = 258
    dictionary = {i: bytes([i]) for i in range(256)}
    result = bytearray()
    data_bits = 0
    bit_count = 0
    pos = 0

    def get_code():
        nonlocal data_bits, bit_count, pos
        while bit_count < code_size and pos < len(data):
            data_bits |= data[pos] << bit_count
            bit_count += 8
            pos += 1
        code = data_bits & ((1 << code_size) - 1)
        data_bits >>= code_size
        bit_count -= code_size
        return code

    prev = None
    while True:
        code = get_code()
        if code == CLEAR:
            dictionary = {i: bytes([i]) for i in range(256)}
            dict_size = 258
            code_size = 9
            prev = None
            continue
        if code == EOI:
            break
        if code in dictionary:
            entry = dictionary[code]
        elif code == dict_size and prev is not None:
            entry = dictionary[prev] + dictionary[prev][:1]
        else:
            raise ValueError("Bad LZW code")
        result.extend(entry)
        if prev is not None:
            dictionary[dict_size] = dictionary[prev] + entry[:1]
            dict_size += 1
            if dict_size == (1 << code_size) and code_size < 12:
                code_size += 1
        prev = code
    return bytes(result)

# Index: (R, G, B) in 0–255 range
ega_palette = [
    (0, 0, 0),         # 0 black
    (0, 0, 170),       # 1 blue (deep water)
    (0, 170, 0),       # 2 green (grass)
    (0, 170, 170),     # 3 cyan (shallow water)
    (170, 0, 0),       # 4 red
    (170, 0, 170),     # 5 magenta
    (170, 85, 0),      # 6 brown (mountains)
    (170, 170, 170),   # 7 light grey
    (85, 85, 85),      # 8 dark grey
    (85, 85, 255),     # 9 bright blue
    (85, 255, 85),     # 10 bright green
    (85, 255, 255),    # 11 bright cyan
    (255, 85, 85),     # 12 bright red
    (255, 85, 255),    # 13 bright magenta
    (255, 255, 85),    # 14 yellow (sand)
    (255, 255, 255),   # 15 white
]

# --- Load 16-colour tileset ---
def load_tiles16(path):
    raw = Path(path).read_bytes()
    (uncomp_len,) = struct.unpack("<I", raw[:4])
    data = lzw_decompress(raw[4:])
    assert len(data) == uncomp_len
    tiles = []
    row_bytes = 8  # 16 pixels @ 4bpp = 8 bytes
    for t in range(512):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        for y in range(TILE_SIZE):
            row = data[t*row_bytes*TILE_SIZE + y*row_bytes : t*row_bytes*TILE_SIZE + (y+1)*row_bytes]
            for x in range(TILE_SIZE):
                shift = 4 if (x % 2) == 0 else 0
                val = (row[x//2] >> shift) & 0x0F
                # Placeholder palette: greyscale; replace with real U5 EGA palette if desired
                colour = ega_palette[val]

                surf.set_at((x, y), colour)
        tiles.append(surf)
    return tiles

# --- Expand BRIT.DAT using chunk map ---
def load_pc_brit_map(data_ovl_path, brit_dat_path):
    ovl = Path(data_ovl_path).read_bytes()
    chunk_map = list(ovl[HEADER_OFF:HEADER_OFF+HEADER_LEN])

    chunks_data = Path(brit_dat_path).read_bytes()
    chunk_list = [chunks_data[i*256:(i+1)*256] for i in range(len(chunks_data)//256)]

    # Prebuild a 16×16 ocean chunk (tile ID 0x01)
    ocean_chunk = bytes([0x01] * (CHUNK_DIM * CHUNK_DIM))

    tiles = bytearray(MAP_DIM * MAP_DIM)
    for gy in range(GRID_DIM):
        for gx in range(GRID_DIM):
            cid = chunk_map[gy*GRID_DIM + gx]
            if cid == VOID_MARKER or cid >= len(chunk_list):
                chunk = ocean_chunk
            else:
                chunk = chunk_list[cid]
            for cy in range(CHUNK_DIM):
                dst = (gy*CHUNK_DIM + cy) * MAP_DIM + gx*CHUNK_DIM
                src = cy * CHUNK_DIM
                tiles[dst:dst+CHUNK_DIM] = chunk[src:src+CHUNK_DIM]
    return tiles

# --- Render full map with tileset ---
def render_map(tiles_ids, tileset, out_file):
    pygame.init()
    surf = pygame.Surface((MAP_DIM*TILE_SIZE, MAP_DIM*TILE_SIZE))
    for y in range(MAP_DIM):
        for x in range(MAP_DIM):
            tid = tiles_ids[y*MAP_DIM + x]
            if 0 <= tid < len(tileset):
                surf.blit(tileset[tid], (x*TILE_SIZE, y*TILE_SIZE))
    pygame.image.save(surf, out_file)
    print(f"Saved {out_file}")

if __name__ == "__main__":
    tile_ids = load_pc_brit_map(DATA_OVL_PATH, BRIT_DAT_PATH)
    tileset = load_tiles16(TILES16_PATH)
    render_map(tile_ids, tileset, OUT_FILE)