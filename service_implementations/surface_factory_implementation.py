import threading
import pygame
from dark_libraries.dark_math import Size

class SurfaceFactoryImplementation:

    def create_surface(self, size_in_pixels: Size[int]) -> pygame.Surface:
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        return pygame.Surface(size_in_pixels.to_tuple())
    
