# file: tileset.py
import struct
from pathlib import Path
from typing import List

TILES16_PATH = r".\u5\TILES.16"
TILE_SIZE = 16

TILE_ID_GRASS = 5

_tileset16_cache = {}

# EGA palette (RGB tuples)
ega_palette = [
    (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
    (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
    ( 85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
    (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255),
]

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

def load_tiles16_raw(path: str) -> list[list[list[int]]]:
    """
    Load TILES.16 and return a list of tiles, each tile being a 2D list
    of palette indices (0–15). No Pygame surfaces are created.
    """
    if path not in _tileset16_cache:
        raw = Path(path).read_bytes()
        (uncomp_len,) = struct.unpack("<I", raw[:4])
        data = lzw_decompress(raw[4:])
        assert len(data) == uncomp_len

        tiles = []
        row_bytes = TILE_SIZE // 2  # 8 bytes per row for 16px wide
        for t in range(512):
            tile_pixels = []
            base_offset = t * row_bytes * TILE_SIZE
            for y in range(TILE_SIZE):
                row = data[base_offset + y * row_bytes : base_offset + (y + 1) * row_bytes]
                pixel_row = []
                for x in range(TILE_SIZE):
                    shift = 4 if (x % 2) == 0 else 0
                    val = (row[x // 2] >> shift) & 0x0F
                    pixel_row.append(val)
                tile_pixels.append(pixel_row)
            tiles.append(tile_pixels)

        _tileset16_cache[path] = tiles
    return _tileset16_cache[path]

# utility function
def draw_tile_onto_pixel_array(tile: List[List[int]], surf, pixels, palette, offset_x, offset_y):
    for py in range(TILE_SIZE):
        for px in range(TILE_SIZE):
            # Get the pixel color from the tile
            u5_color = tile[py][px]
            rgb_color = palette[u5_color]
            # Set the pixel color on the rendered surface
            pixels[(offset_x + px, offset_y + py)] = surf.map_rgb(rgb_color)

if __name__ == "__main__":
    import pygame

    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms
    tileset_raw = load_tiles16_raw(TILES16_PATH)

    TILE_SCALE = 2
    GRID_COLS = 32
    GRID_ROWS = 16
    MARGIN = 10  # padding around grid

    win_w = GRID_COLS * TILE_SIZE * TILE_SCALE + MARGIN * 2
    win_h = GRID_ROWS * TILE_SIZE * TILE_SCALE + MARGIN * 2 + 30
    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("U5 Sprite Viewer")

    font = pygame.font.SysFont(None, 20)

    active_row, active_col = 0, 0  # cursor position in grid
    start_index = 0                # index of top-left tile in grid

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    active_col = (active_col + 1) % GRID_COLS
                elif event.key == pygame.K_LEFT:
                    active_col = (active_col - 1) % GRID_COLS
                elif event.key == pygame.K_DOWN:
                    active_row = (active_row + 1) % GRID_ROWS
                elif event.key == pygame.K_UP:
                    active_row = (active_row - 1) % GRID_ROWS

        screen.fill((30, 30, 30))

        # Draw tiles in grid
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                idx = start_index + row * GRID_COLS + col
                if idx >= len(tileset_raw):
                    continue
                raw_tile = tileset_raw[idx]
                surf_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
                pixels_tile = pygame.PixelArray(surf_tile)
                draw_tile_onto_pixel_array(raw_tile, surf_tile, pixels_tile, ega_palette, 0, 0)
                del pixels_tile
                sprite_img = pygame.transform.scale(
                    surf_tile,
                    (TILE_SIZE * TILE_SCALE, TILE_SIZE * TILE_SCALE)
                )
                x = MARGIN + col * TILE_SIZE * TILE_SCALE
                y = MARGIN + row * TILE_SIZE * TILE_SCALE
                screen.blit(sprite_img, (x, y))

        # Cursor rectangle
        cursor_x = MARGIN + active_col * TILE_SIZE * TILE_SCALE
        cursor_y = MARGIN + active_row * TILE_SIZE * TILE_SCALE
        cursor_rect = pygame.Rect(
            cursor_x, cursor_y, TILE_SIZE * TILE_SCALE, TILE_SIZE * TILE_SCALE
        )
        pygame.draw.rect(screen, (255, 0, 0), cursor_rect, width=3)

        # Show active tile index
        active_index = start_index + active_row * GRID_COLS + active_col
        text_surf = font.render(f"Tile {active_index}", True, (255, 255, 255))
        screen.blit(
            text_surf,
            (MARGIN, GRID_ROWS * TILE_SIZE * TILE_SCALE + MARGIN + 5)
        )

        pygame.display.flip()