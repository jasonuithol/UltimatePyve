# file: maps/tileset.py
import pygame, struct
from pathlib import Path

from dark_libraries.custom_decorators import auto_init
from dark_libraries.dark_math import Coord, Size

from .display_config import DisplayConfig, EgaPalette

TILE_ID_GRASS = 5

'''
class EgaPalette(List[Tuple[int,int,int]]):
    pass

# EGA palette (RGB tuples)
_ega_palette = EgaPalette([
    (0, 0, 0),         # 0000: Black
    (0, 0, 170),       # 0001: Blue
    (0, 170, 0),       # 0010: Green
    (0, 170, 170),     # 0011: Cyan

    (170, 0, 0),       # 0100: Red
    (170, 0, 170),     # 0101: Magenta
    (170, 85, 0),      # 0110: Brown (dark yellow)
    (170, 170, 170),   # 0111: Light Gray

    (85, 85, 85),      # 1000: Dark Gray
    (85, 85, 255),     # 1001: Light Blue
    (85, 255, 85),     # 1010: Light Green
    (85, 255, 255),    # 1011: Light Cyan

    (255, 85, 85),     # 1100: Light Red
    (255, 85, 255),    # 1101: Light Magenta
    (255, 255, 85),    # 1110: Yellow
    (255, 255, 255),   # 1111: White
])
'''

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

TileData = list[list[int]]

@auto_init
class Tile:
    tile_id: int
    pixels: TileData | None = None
    surface: pygame.Surface | None = None

    def _get_size(self):
        return Size(len(self.pixels[0]), len(self.pixels))

    def _draw_onto_pixel_array(self, surface_pixels:pygame.PixelArray, palette: EgaPalette, target_pixel_offset: Coord = Coord(0,0)):

        for pixel_coord in self._get_size():

            # Get the pixel color from the tile
            u5_color = self.pixels[pixel_coord.y][pixel_coord.x]
            rgb_color = palette[u5_color]
            
            # Set the pixel color on the rendered surface
            surface_pixels[pixel_coord.add(target_pixel_offset).to_tuple()] = surface_pixels.surface.map_rgb(rgb_color)
                
    def create_surface(self, palette: EgaPalette):
        self.surface = pygame.Surface(self._get_size().to_tuple())
        surface_pixels = pygame.PixelArray(self.surface)
        self._draw_onto_pixel_array(surface_pixels, palette)
        del surface_pixels

    def set_surface(self, surface):
        self.surface = surface

    def get_surface(self):
        return self.surface

    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord = Coord(0,0)):
        target_rectangle = self.surface.get_rect()
        target_rectangle.topleft = pixel_offset.to_tuple()

        target_surface.blit(self.surface, target_rectangle)

class TileRegistry:
    def _after_inject(self):
        self.tiles: dict[int,Tile] = {}

    def register_tile(self, tile_id: int, tile: Tile):
        self.tiles[tile_id] = tile

    def get_tile(self, tile_id: int) -> Tile:
        return self.tiles[tile_id]

class TileLoader:

    TOTAL_TILES = 512

    display_config: DisplayConfig
    registry: TileRegistry
 
    def tile_from_bytes(self, tile_id: int, data:bytes) -> Tile:

        TILE_SIZE = self.display_config.TILE_SIZE

        pixels: TileData = []
        ROW_BYTES = TILE_SIZE.w // 2

        base_offset = tile_id * ROW_BYTES * TILE_SIZE.h
        for y in range(TILE_SIZE.h):
            row = data[base_offset + y * ROW_BYTES : base_offset + (y + 1) * ROW_BYTES]
            pixel_row = []
            for x in range(TILE_SIZE.w):
                shift = 4 if (x % 2) == 0 else 0
                val = (row[x // 2] >> shift) & 0x0F
                pixel_row.append(val)
            pixels.append(pixel_row)

        tile = Tile(tile_id, pixels)
        tile.create_surface(self.display_config.EGA_PALETTE)
        return tile

    def load_tiles(self):
        path = Path("u5/TILES.16")
        raw = path.read_bytes()
        (uncomp_len,) = struct.unpack("<I", raw[:4])
        data = lzw_decompress(raw[4:])
        assert len(data) == uncomp_len, f"Expected {uncomp_len} bytes after decompressing, but got {len(data)} bytes."

        for tile_id in range(512):
            tile = self.tile_from_bytes(tile_id, data)
            self.registry.register_tile(tile_id, tile)

        print(f"[tileset] Loaded {len(self.registry.tiles)} tiles from {path}")
    
if __name__ == "__main__":
    import pygame

    pygame.init()
    pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

    tile_loader = TileLoader()
    tile_loader.display_config = DisplayConfig()
    tile_loader.registry = TileRegistry()
    tile_loader.registry._after_inject()
    tile_loader.load_tiles()

    # Override scale factor
    tile_loader.display_config.SCALE_FACTOR = 3

    GRID_COLS = 40
    GRID_ROWS = (TileLoader.TOTAL_TILES // GRID_COLS) + 1
    MARGIN = 10  # padding around grid

    win_w = GRID_COLS * tile_loader.display_config.TILE_SIZE.w * tile_loader.display_config.SCALE_FACTOR + MARGIN * 2
    win_h = GRID_ROWS * tile_loader.display_config.TILE_SIZE.h * tile_loader.display_config.SCALE_FACTOR + MARGIN * 2 + 30

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption("U5 Sprite Viewer")
    pygame.scrap.init()

    font = pygame.font.SysFont(None, 20)

    active_row, active_col = 0, 0  # cursor position in grid
    start_index = 0                # index of top-left tile in grid

    # Button geometry
    btn_w, btn_h = 100, 24
    btn_x = win_w - btn_w - MARGIN
    btn_y = win_h - btn_h - MARGIN
    button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

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
            '''
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos):
                    active_index = start_index + active_row * GRID_COLS + active_col
                    raw_tile: Tile = tileset_raw[active_index]

                    # Flatten 2D list of rows into a single list of ints
                    flat_bytes = bytes([pix for row in raw_tile.pixels for pix in row])
                    b64 = base64.b64encode(flat_bytes).decode("ascii")

                    pygame.scrap.put(pygame.SCRAP_TEXT, b64.encode("utf-8"))
                    print(f"Copied Tile {active_index} to clipboard (base64)")
            '''

        screen.fill((30, 30, 30))
        scaled_size = tile_loader.display_config.TILE_SIZE.scale(tile_loader.display_config.SCALE_FACTOR)

        # Draw tiles in grid
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                tile_id = start_index + row * GRID_COLS + col
                if tile_id >= len(tile_loader.registry.tiles):
                    continue
                tile = tile_loader.registry.get_tile(tile_id)
                surf_tile = tile.get_surface()
                sprite_img = pygame.transform.scale(
                    surf_tile,
                    scaled_size.to_tuple()
                )
                x = MARGIN + col * scaled_size.w
                y = MARGIN + row * scaled_size.h
                screen.blit(sprite_img, (x, y))

        # Cursor rectangle
        cursor_x = MARGIN + active_col * scaled_size.w
        cursor_y = MARGIN + active_row * scaled_size.h
        cursor_rect = pygame.Rect(
            cursor_x, cursor_y, scaled_size.w, scaled_size.h
        )
        pygame.draw.rect(screen, (255, 0, 0), cursor_rect, width=3)

        # Show active tile index
        active_index = start_index + active_row * GRID_COLS + active_col
        text_surf = font.render(f"Tile {active_index}", True, (255, 255, 255))
        screen.blit(
            text_surf,
            (MARGIN, GRID_ROWS * scaled_size.h + MARGIN + 5)
        )

        # Draw copy button
        pygame.draw.rect(screen, (0, 0, 0), button_rect)
        pygame.draw.rect(screen, (255, 0, 0), button_rect, width=2)
        btn_label = font.render("Copy Base64", True, (255, 255, 255))
        label_rect = btn_label.get_rect(center=button_rect.center)
        screen.blit(btn_label, label_rect)

        pygame.display.flip()

