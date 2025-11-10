import threading
import pygame
from dark_libraries.dark_math import Coord, Rect
from dark_libraries.dark_surface import DarkSurface
from dark_libraries.logging import LoggerMixin

from models.tile import Tile

from .display_config import DisplayConfig
from .scalable_component import ScalableComponent

BIBLICALLY_ACCURATE_MISC_LINE_THICCNESS = 2

class ViewPort(ScalableComponent, LoggerMixin):

    # Injectable Properties
    display_config: DisplayConfig

    def __init__(self):
        #LoggerMixin.__init__(self)
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.VIEW_PORT_SIZE.scale(self.display_config.TILE_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )
        super()._after_inject()
        self._combat_view_rect = Rect(Coord(-3,-3), self.display_config.VIEW_PORT_SIZE)

    def clear(self):
        self._clear()

    def draw_tile_to_view_coord(self, view_coord: Coord[int], tile: Tile, inverted: bool):

        assert tile, f"Tile cannot be None.  view_coord={view_coord}, inverted={inverted}"
        unscaled_pixel_coord = view_coord * self.display_config.TILE_SIZE
        self.draw_object_at_unscaled_coord(unscaled_pixel_coord, tile, inverted)

    def draw_object_at_unscaled_coord(self, unscaled_pixel_coord: Coord[int], dark_surface: DarkSurface, inverted: bool):

        dark_surface.blit_to_surface(
            target_surface = self.get_input_surface(), 
            pixel_offset   = unscaled_pixel_coord,
            inverted       = inverted
        )

    def draw_unscaled_line(self, start_coord: Coord[int], end_coord: Coord[int], rgb_mapped_color: int):
        assert threading.current_thread() is threading.main_thread(), "Cannot call this method from a worker thread"
        pygame.draw.line(
            surface   = self.get_input_surface(),
            color     = rgb_mapped_color,
            start_pos = start_coord,
            end_pos   = end_coord,
            width = BIBLICALLY_ACCURATE_MISC_LINE_THICCNESS
        )
        
