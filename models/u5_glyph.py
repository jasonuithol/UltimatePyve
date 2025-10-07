import pygame

from typing import Self

from dark_libraries.custom_decorators import immutable
from dark_libraries.dark_math import Coord, Size

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