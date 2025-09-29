from pathlib import Path
from typing import Self

import pygame
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord, Size

@immutable
@auto_init
class U5Font:
    data: list[bytearray]
    char_size: Size

    def map_codes(self, msg: list[int]) -> list[bytearray]:
        glyphs: list[bytearray] = []
        for code in msg:
            assert code < len(self.data), f"unmappable code={code} exceeds length of font {len(self.data)})"
            glyphs.append(self.data[code])
        return glyphs

    def map_string(self, msg: str) -> list[bytearray]:
        codes: list[int] = []
        for char in msg:
            ascii_code = ord(char)
            assert ascii_code < len(self.data), f"unmappable character {char} (code={ascii_code} exceeds length of font {len(self.data)})"
            codes.append(ascii_code)
        return self.map_codes(codes)

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

#        overlay._surface.blit(result._surface, (0,0))
        result._surface.blit(overlay._surface, (0,0))
        
        overlay._surface.set_colorkey(existing_color_key)
        return result

class U5FontRegistry:
    def _after_inject(self):
        self.fonts: dict[str, U5Font] = {}

    def register_font(self, name: str, u5font: U5Font):
        self.fonts[name] = u5font

    def get_font(self, str):
        return self.fonts[str]

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

        print(f"[fonts] Loaded {len(data)} font glyphs from {name}")

        return U5Font(data, char_size)
    
    def register_fonts(self):
        for font_name in ["IBM.CH", "RUNES.CH"]:
            font = self.load(font_name, Size(8,8))
            self.registry.register_font(font_name, font)
