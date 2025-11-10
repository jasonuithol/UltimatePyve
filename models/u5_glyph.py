import threading
import pygame

from typing import Self

from dark_libraries.dark_math import Coord
from dark_libraries.dark_surface import DarkSurface
from models.enums.ega_palette_values import EgaPaletteValues

class U5Glyph(tuple, DarkSurface):

    @classmethod
    def from_surface(cls, surface: pygame.Surface) -> Self:
        return tuple.__new__(cls, (surface, None))

    def __new__(cls, surface: pygame.Surface):
        return cls.from_surface(surface)

    @property
    def _surface(self) -> pygame.Surface:
        return self[0]

    # IMPLEMENTATION START: DarkSurface
    #
    def get_surface(self, inverted = False) -> pygame.Surface:
        return self._surface

    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord[int], inverted = False):
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        target_surface.blit(
            source = self._surface,
            dest   = pixel_offset.to_tuple()
        )
    #
    # IMPLEMENTATION FINISH: DarkSurface

    def blit_at_char_coord(self, char_coord: Coord[int], target: pygame.Surface):
        pixel_coord: Coord[int] = char_coord * self._surface.get_size()
        self.blit_to_surface(target, pixel_coord)

    def rotate_90(self) -> Self:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        new_surface = pygame.transform.rotate(self._surface, 90)
        return __class__.from_surface(new_surface)

    def flip(self, flip_x: bool = False, flip_y: bool = False) -> Self:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        new_surface = pygame.transform.flip(self._surface, flip_x, flip_y)
        return __class__.from_surface(new_surface)
    
    def overlay_with(self, overlay: Self, transparent_mapped_rgb: int) -> Self:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        existing_color_key = overlay._surface.get_colorkey()
        overlay._surface.set_colorkey(transparent_mapped_rgb)

        new_surface = self._surface.copy()
        new_surface.blit(source = overlay._surface, dest = (0,0))
        overlay._surface.set_colorkey(existing_color_key)

        return __class__.from_surface(new_surface)

    def replace_color(self, old_mapped_rgb: int, new_mapped_rbg: int) -> Self:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"

        new_surface = self._surface.copy()

        pa = pygame.PixelArray(new_surface)
        pa.replace(old_mapped_rgb, new_mapped_rbg)
        del pa

        return __class__.from_surface(new_surface)
    
    def invert_colors(self) -> Self:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"

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
