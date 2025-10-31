# file: maps/tileset.py
import pygame, struct
from pathlib import Path

from dark_libraries.dark_math import Coord
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues
from models.tile import Tile, TileData
from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig

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

class TileLoader(LoggerMixin):

    TOTAL_TILES = 512

    display_config: DisplayConfig
    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory
 
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
        surf = self._create_surface(tile)
        tile.set_surface(surf)
        return tile

    def _create_surface(self, tile: Tile) -> pygame.Surface:
        assert tile.surface is None, "Surface already created !"

        #
        # TODO: use SurfaceFactory
        #
        surface = self.surface_factory.create_surface(tile._get_size())
        surface_pixels = pygame.PixelArray(surface)
        self._draw_onto_pixel_array(tile, surface_pixels)
        del surface_pixels
        return surface

    def _draw_onto_pixel_array(self, tile: Tile, surface_pixels : pygame.PixelArray, target_pixel_offset: Coord[int] = Coord[int](0,0)):

        for pixel_coord in tile._get_size():

            # Get the pixel color from the tile
            u5_color = tile.pixels[pixel_coord.y][pixel_coord.x]
            ega_color = EgaPaletteValues.from_index(u5_color)
            rgb_color = self.global_registry.colors.get(ega_color)
            
            # Set the pixel color on the rendered surface
            surface_pixels[pixel_coord.add(target_pixel_offset).to_tuple()] = rgb_color

    def load_tiles(self, u5_path: Path):
        path = u5_path.joinpath("TILES.16")
        raw = path.read_bytes()
        (uncomp_len,) = struct.unpack("<I", raw[:4])
        data = lzw_decompress(raw[4:])
        assert len(data) == uncomp_len, f"Expected {uncomp_len} bytes after decompressing, but got {len(data)} bytes."

        for tile_id in range(512):
            tile = self.tile_from_bytes(tile_id, data)
            self.global_registry.tiles.register(tile_id, tile)

        self.log(f"Loaded {len(self.global_registry.tiles)} tiles from {path}")
    


