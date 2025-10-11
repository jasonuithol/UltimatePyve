from typing import Iterable
from dark_libraries.dark_math import Coord

from models.u5_glyph import U5Glyph
from view.display_config import DisplayConfig
from view.scalable_component import ScalableComponent

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig

    def __init__(self):
        self._cursor: int = 0

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

    def _scroll(self, lines: int = 1):
        self.scroll_dy(self.display_config.FONT_SIZE.h * lines * -1)

    def _return(self):
        self._cursor = 0

    def _advance(self):
        self._cursor += 1

    def print_glyphs(self, glyphs: Iterable[U5Glyph], include_carriage_return: bool = True):

        target = self.get_input_surface()
        for glyph in glyphs:
            if self._cursor >= self.display_config.CONSOLE_SIZE.w:
                self._scroll()
                self._return()
            char_coord = Coord(self._cursor, self.display_config.CONSOLE_SIZE.h - 1)
            glyph.blit_to_surface(char_coord, target)
            self._advance()

        if include_carriage_return:
            self._scroll()
            self._scroll()
            self._return()
