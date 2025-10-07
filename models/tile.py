import pygame

from dark_libraries.custom_decorators import auto_init
from dark_libraries.dark_math import Coord, Size
from view.display_config import EgaPalette

TILE_ID_GRASS = 5

type TileData = list[list[int]]

@auto_init
class Tile:
    tile_id: int
    pixels: TileData | None = None
    surface: pygame.Surface | None = None

    # WARNING: Not the fastest ever.
    def _get_size(self):
        return Size(len(self.pixels[0]), len(self.pixels))

    def _draw_onto_pixel_array(self, surface_pixels:pygame.PixelArray, palette: EgaPalette, target_pixel_offset: Coord = Coord(0,0)):

        for pixel_coord in self._get_size():

            # Get the pixel color from the tile
            u5_color = self.pixels[pixel_coord.y][pixel_coord.x]
            rgb_color = palette[u5_color]
            
            # Set the pixel color on the rendered surface
            surface_pixels[pixel_coord.add(target_pixel_offset).to_tuple()] = surface_pixels.surface.map_rgb(rgb_color)
                
    def create_surface(self, palette: EgaPalette):
        assert self.surface is None, "Surface already created !"
        surface = pygame.Surface(self._get_size().to_tuple())
        surface_pixels = pygame.PixelArray(surface)
        self._draw_onto_pixel_array(surface_pixels, palette)
        del surface_pixels
        self.set_surface(surface)

    def set_surface(self, surface: pygame.Surface):
        self.surface = surface

    def get_surface(self) -> pygame.Surface:
        return self.surface

    def blit_to_surface(self, target_surface: pygame.Surface, pixel_offset: Coord = Coord(0,0)):
        target_surface.blit(self.surface, pixel_offset.to_tuple())