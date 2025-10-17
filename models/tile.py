import pygame

from dark_libraries.dark_math import Coord, Size

TILE_ID_GRASS = 5
TILE_ID_BLACK = 255

type TileData = list[list[int]]

class Tile:

    def __init__(self, tile_id: int, pixels: TileData = None, surface: pygame.Surface = None):
        self.tile_id = tile_id
        self.pixels  = pixels
        self.surface = surface

    # WARNING: Not the fastest ever.
    def _get_size(self):
        return Size(len(self.pixels[0]), len(self.pixels))

    def set_surface(self, surface: pygame.Surface):
        self.surface = surface

    def get_surface(self) -> pygame.Surface:
        return self.surface

    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord = Coord(0,0)):
        target_surface.blit(self.surface, pixel_offset.to_tuple())