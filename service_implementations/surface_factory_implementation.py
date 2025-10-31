import pygame
from dark_libraries.dark_math import Size

class SurfaceFactoryImplementation:

    def create_surface(self, size_in_pixels: Size[int]) -> pygame.Surface:
        return pygame.Surface(size_in_pixels.to_tuple())
    
