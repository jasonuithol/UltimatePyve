import pygame

from dark_libraries.dark_math import Size
from models.enums.ega_palette_values import EgaPaletteValues
from services.surface_factory import SurfaceFactory

class ScalableComponent:

    # Injectable
    surface_factory: SurfaceFactory

    def __init__(self, unscaled_size_in_pixels: Size, scale_factor: int):
        super().__init__()
        self._unscaled_size_in_pixels = unscaled_size_in_pixels
        self._scale_factor = scale_factor

    def _after_inject(self):
        self._unscaled_surface = self.surface_factory.create_surface(self._unscaled_size_in_pixels)
        self._scaled_surface   = self.surface_factory.create_surface(self._unscaled_size_in_pixels.scale(self._scale_factor))
        self._back_color       = self.surface_factory.get_rgb_mapped_color(EgaPaletteValues.Black)

    def _clear(self):
        self._scaled_surface.fill(self._back_color)
        self._unscaled_surface.fill(self._back_color)

    def unscaled_size(self) -> Size:
        return self._unscaled_size_in_pixels
    
    def scaled_size(self) -> Size:
        return self._unscaled_size_in_pixels.scale(self._scale_factor)

    def get_input_surface(self) -> pygame.Surface:
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:
        pygame.transform.scale_by(
            surface      = self._unscaled_surface,
            factor       = self._scale_factor,
            dest_surface = self._scaled_surface
        )
        return self._scaled_surface
   
    def scroll_dx(self, dx: int):
        self._unscaled_surface.scroll(dx = dx, dy = 0)
        fill_rect = (
            (self._unscaled_size_in_pixels.w + dx) % self._unscaled_size_in_pixels.w,
            0,
            abs(dx),
            self._unscaled_size_in_pixels.h
        )
        self._unscaled_surface.fill(self._back_color, fill_rect)

    def scroll_dy(self, dy: int):
        self._unscaled_surface.scroll(dx = 0, dy = dy)
        fill_rect = (
            0,
            (self._unscaled_size_in_pixels.h + dy) % self._unscaled_size_in_pixels.h,
            self._unscaled_size_in_pixels.w,
            abs(dy)
        )
        self._unscaled_surface.fill(self._back_color, fill_rect)
       