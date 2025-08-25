# file: tileset.py
import struct, pygame
from pathlib import Path

TILE_SIZE = 16

# --- LZW decompression ---
def lzw_decompress(data: bytes) -> bytes:
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

# EGA palette
ega_palette = [
    (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
    (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
    (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
    (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255),
]

def load_tiles16(path: str) -> list[pygame.Surface]:
    raw = Path(path).read_bytes()
    (uncomp_len,) = struct.unpack("<I", raw[:4])
    data = lzw_decompress(raw[4:])
    assert len(data) == uncomp_len
    tiles = []
    row_bytes = 8
    for t in range(512):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        for y in range(TILE_SIZE):
            row = data[t*row_bytes*TILE_SIZE + y*row_bytes :
                       t*row_bytes*TILE_SIZE + (y+1)*row_bytes]
            for x in range(TILE_SIZE):
                shift = 4 if (x % 2) == 0 else 0
                val = (row[x//2] >> shift) & 0x0F
                surf.set_at((x, y), ega_palette[val])
        tiles.append(surf)
    return tiles