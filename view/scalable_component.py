import pygame

from dark_libraries.dark_math import Size
from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues
from services.surface_factory import SurfaceFactory

class ScalableComponent:

    # Injectable
    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory

    def __init__(self, unscaled_size_in_pixels: Size[int], scale_factor: int, **kwargs):
        super().__init__(**kwargs)
        self._unscaled_size_in_pixels = unscaled_size_in_pixels
        self._scale_factor = scale_factor

    def _after_inject(self):
        self._unscaled_surface = self.surface_factory.create_surface(self._unscaled_size_in_pixels)
        self._scaled_surface   = self.surface_factory.create_surface(self._unscaled_size_in_pixels.scale(self._scale_factor))
        self._back_color       = EgaPaletteValues.Black

    def _rgb_back_color(self) -> int:
        return self.global_registry.colors.get(self._back_color)

    def _clear(self):
        rgb_mapped = self._rgb_back_color()
        self._scaled_surface.fill(rgb_mapped)
        self._unscaled_surface.fill(rgb_mapped)

    def unscaled_size(self) -> Size[int]:
        return self._unscaled_size_in_pixels
    
    def scaled_size(self) -> Size[int]:
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
        self._unscaled_surface.fill(self._rgb_back_color(), fill_rect)
       