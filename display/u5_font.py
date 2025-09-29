from pathlib import Path
from typing import Self

import pygame
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord, Size
from display.display_config import DisplayConfig

@immutable
@auto_init
class U5Font:
    data: list[bytearray]
    char_size: Size

@immutable
class U5Glyph:
    
    def __init__(self, data: bytearray, glyph_size: Size, foreground_color_mapped_rgb: int, background_color_mapped_rgb: int):
        self._surface = pygame.Surface(glyph_size.to_tuple())
        target = pygame.PixelArray(self._surface)
        for y in range(glyph_size.h):
            for x in range(glyph_size.w):
                bit_index = x + (y * glyph_size.h)
                byte_index = bit_index // 8
                bit_offset = bit_index % 8
                bit_value = data[byte_index] & (1 << (8 - bit_offset))
                target[x, y] = foreground_color_mapped_rgb if bit_value else background_color_mapped_rgb        
        del target

    def blit_to_surface(self, char_coord: Coord, target: pygame.Surface):
        origin_x, origin_y = char_coord.x * self._surface.get_width(), char_coord.y * self._surface.get_height()
        target.blit(
            source = self._surface,
            dest   = (origin_x, origin_y)
        )

    def rotate_90(self) -> Self:
        rotated = object.__new__(self.__class__)
        rotated._surface = pygame.transform.rotate(self._surface, 90)
        return rotated

#    def set_transparent_color(self, mapped_rgb_color: int):
#        self._surface.set_colorkey(mapped_rgb_color)

    def copy(self) -> Self:
        clone = object.__new__(self.__class__)
        clone._surface = self._surface.copy()
        return clone
    
    def overlay_with(self, overlay: Self, transparent_mapped_rgb: int) -> Self:
        existing_color_key = overlay._surface.get_colorkey()
        result = self.copy()
        overlay._surface.set_colorkey(transparent_mapped_rgb)
        result._surface.blit(source = overlay._surface, dest = (0,0))
        overlay._surface.set_colorkey(existing_color_key)
        return result

    def replace_color(self, old_mapped_rgb: int, new_mapped_rbg: int) -> Self:
        new_glyph = self.copy()
        pa = pygame.PixelArray(new_glyph._surface)
        pa.replace(old_mapped_rgb, new_mapped_rbg)
        del pa
        return new_glyph

class U5FontRegistry:
    def _after_inject(self):
        self.fonts: dict[str, U5Font] = {}

    def register_font(self, name: str, u5font: U5Font):
        self.fonts[name] = u5font

    def get_font(self, str):
        return self.fonts[str]

class U5GlyphRegistry:

    def _after_inject(self):
        self.glyphs: dict[tuple[str, int], U5Glyph] = {}

    def register_glyph(self, font_name: str, glyph_code: int, u5glyph: U5Glyph):
        self.glyphs[(font_name, glyph_code)] = u5glyph

    def get_glyph(self, font_name: str, glyph_code: int):
        return self.glyphs[(font_name, glyph_code)]
    
    def map_string_to_glyphs(self, font_name: str, message: str):
        return [self.get_glyph(font_name, ord(char)) for char in message]

    def map_codes_to_glyphs(self, font_name: str, glyph_codes: list[int]):
        return [self.get_glyph(font_name, glyph_code) for glyph_code in glyph_codes]

class U5FontLoader:

    # Injectable
    registry: U5FontRegistry

    def load(self, name: str, char_size: Size) -> U5Font:
        path = Path(f"u5/{name}")
        ba = path.read_bytes()
        char_length_in_bytes = (char_size.w * char_size.h) // 8
        data = []
        for index in range(len(ba) // char_length_in_bytes):
            data.append(ba[(index * 8):(index * 8) + char_length_in_bytes])

        print(f"[fonts] Loaded {len(data)} font data blobs from {name}")

        return U5Font(data, char_size)
    
    def register_fonts(self):
        for font_name in ["IBM.CH", "RUNES.CH"]:
            font = self.load(font_name, Size(8,8))
            self.registry.register_font(font_name, font)

class U5GlyphLoader:

    # Injectable
    display_config: DisplayConfig
    u5_font_registry: U5FontRegistry
    u5_glyph_registry: U5GlyphRegistry

    def register_glyphs(self):
        surf = pygame.Surface((1,1))
        white = surf.map_rgb(self.display_config.EGA_PALETTE[15])
        black = surf.map_rgb(self.display_config.EGA_PALETTE[00])
        for font_name, font in self.u5_font_registry.fonts.items():
            for glyph_code, glyph_data in enumerate(font.data):
                glyph = U5Glyph(
                    data = glyph_data,
                    glyph_size = self.display_config.FONT_SIZE,
                    foreground_color_mapped_rgb = white,
                    background_color_mapped_rgb = black
                )
                self.u5_glyph_registry.register_glyph(font_name, glyph_code, glyph)
            print(f"[fonts] Registered {len(list(filter(lambda glyph_key: glyph_key[0] == font_name, self.u5_glyph_registry.glyphs.keys())))} u5glyphs from {font_name}")
