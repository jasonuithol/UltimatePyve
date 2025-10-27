import pygame
from dark_libraries.dark_math import Size
from models.enums.ega_palette_values import EgaPaletteValues
from view.display_config import DisplayConfig

class SurfaceFactory:

    display_config: DisplayConfig

    # must be called after pygame.init()
    def init(self):
        self._build_palette_rgbs()

    def _build_palette_rgbs(self):
        s = self.create_surface(Size[int](1,1))
        self._rgb_color_map = {
            color : s.map_rgb(color.value)
            for color in EgaPaletteValues
        }
        self._rgb_index_map = {
            index : s.map_rgb(color.value)
            for index, color in enumerate(EgaPaletteValues)
        }
    
    def create_surface(self, size_in_pixels: Size[int]) -> pygame.Surface:
        return pygame.Surface(size_in_pixels.to_tuple()).convert()
    
    def get_rgb_mapped_color(self, color: EgaPaletteValues | int):
        if isinstance(color, EgaPaletteValues):
            return self._rgb_color_map[color]
        else:
            return self._rgb_index_map[color]