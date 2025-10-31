import pygame
from typing import Protocol
from dark_libraries.dark_math import Size

class SurfaceFactory(Protocol):

    def create_surface(self, size_in_pixels: Size[int]) -> pygame.Surface: ...
    
