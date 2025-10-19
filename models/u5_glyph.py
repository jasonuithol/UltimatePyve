import pygame

from typing import Self

from dark_libraries.custom_decorators import immutable
from dark_libraries.dark_math import Coord

@immutable
class U5Glyph:

    def __init__(self, surface: pygame.Surface):
        self._surface = surface

    def get_surface(self) -> pygame.Surface:
        return self._surface

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

    def flip(self, flip_x: bool = False, flip_y: bool = False) -> Self:
        bird_recipient = object.__new__(self.__class__)
        bird_recipient._surface = pygame.transform.flip(self._surface, flip_x, flip_y)
        return bird_recipient

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