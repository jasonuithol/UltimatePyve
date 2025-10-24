import pygame

from typing import Self

from dark_libraries.dark_math import Coord
from models.enums.ega_palette_values import EgaPaletteValues

class U5Glyph(tuple):

    @classmethod
    def from_surface(cls, surface: pygame.Surface) -> Self:
        return tuple.__new__(cls, (surface, None))

    def __new__(cls, surface: pygame.Surface):
        return cls.from_surface(surface)

    @property
    def _surface(self) -> pygame.Surface:
        return self[0]

    def get_surface(self) -> pygame.Surface:
        return self._surface

    def blit_to_surface(self, char_coord: Coord, target: pygame.Surface):
        origin_x, origin_y = char_coord.x * self._surface.get_width(), char_coord.y * self._surface.get_height()
        target.blit(
            source = self._surface,
            dest   = (origin_x, origin_y)
        )

    def rotate_90(self) -> Self:
        new_surface = pygame.transform.rotate(self._surface, 90)
        return __class__.from_surface(new_surface)

    def flip(self, flip_x: bool = False, flip_y: bool = False) -> Self:
        new_surface = pygame.transform.flip(self._surface, flip_x, flip_y)
        return __class__.from_surface(new_surface)
    
    def overlay_with(self, overlay: Self, transparent_mapped_rgb: int) -> Self:
        existing_color_key = overlay._surface.get_colorkey()
        overlay._surface.set_colorkey(transparent_mapped_rgb)

        new_surface = self._surface.copy()
        new_surface.blit(source = overlay._surface, dest = (0,0))
        overlay._surface.set_colorkey(existing_color_key)

        return __class__.from_surface(new_surface)

    def replace_color(self, old_mapped_rgb: int, new_mapped_rbg: int) -> Self:

        new_surface = self._surface.copy()

        pa = pygame.PixelArray(new_surface)
        pa.replace(old_mapped_rgb, new_mapped_rbg)
        del pa

        return __class__.from_surface(new_surface)
    
    def invert_colors(self) -> Self:

        new_surface = self._surface.copy()

        white = self._surface.map_rgb(EgaPaletteValues.White.value)
        black = self._surface.map_rgb(EgaPaletteValues.Black.value)
        pa = pygame.PixelArray(new_surface)
        for y in range(self._surface.get_height()):
            for x in range(self._surface.get_width()):
                if pa[x,y] == white:
                    pa[x,y] = black
                else:
                    pa[x,y] = white
        del pa

        return __class__.from_surface(new_surface)
