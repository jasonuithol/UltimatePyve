import pygame
import numpy as np

from dark_libraries.dark_math import Coord, Size
from dark_libraries.dark_surface import DarkSurface

TILE_ID_GRASS = 5
TILE_ID_BLACK = 255

type TileData = list[list[int]]

class Tile(DarkSurface):

    def __init__(self, tile_id: int, pixels: TileData = None, surface: pygame.Surface = None):
        self.tile_id = tile_id
        self.pixels  = pixels
        self.set_surface(surface)

    # WARNING: Not the fastest ever.
    # WARNING: This will break if called on flame sprite tiles or other generated tiles !
    def _get_size(self):
        return Size[int](len(self.pixels[0]), len(self.pixels))

    def set_surface(self, surface: pygame.Surface):
        self.surface = surface

        if surface:
            # Make a color inverted surface
            self.inverted_surface = surface.convert()
            arr = pygame.surfarray.pixels3d(self.inverted_surface)
            np.subtract(255, arr, out=arr)
            del arr

    # IMPLEMENTATION START: DarkSurface
    #
    def get_surface(self, inverted = False) -> pygame.Surface:
        if inverted == True:
            return self.inverted_surface
        else:
            return self.surface

    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord[int] = Coord[int](0,0), inverted = False):
        target_surface.blit(self.get_surface(inverted), pixel_offset.to_tuple())
    #
    # IMPLEMENTATION FINISH: DarkSurface
