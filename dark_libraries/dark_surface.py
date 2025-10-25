from typing import Protocol

import pygame

from dark_libraries.dark_math import Coord

class DarkSurface(Protocol):
    def get_surface(self, inverted = False) -> pygame.Surface:
        ...
    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord[int], inverted = False):
        ...
        