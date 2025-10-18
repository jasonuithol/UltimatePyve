from typing import Iterable
from dark_libraries.dark_math import Coord, Vector2

from models.u5_glyph import U5Glyph
from view.border_drawer_factory import BorderDrawer, BorderDrawerFactory
from view.display_config import DisplayConfig
from view.scalable_component import ScalableComponent

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
    border_drawer_factory: BorderDrawerFactory

    def __init__(self):
        self._cursor: int = 0
        self._border_drawer: BorderDrawer = None

    def _after_inject(self):
        super().__init__(self.display_config.CONSOLE_SIZE * self.display_config.FONT_SIZE, self.display_config.SCALE_FACTOR)
        super()._after_inject()
        self._cursor_y = self.display_config.CONSOLE_SIZE.h - 1

    def _scroll(self, lines: int = 1):
        self.scroll_dy(self.display_config.FONT_SIZE.h * lines * -1)

    def _return(self):
        self._cursor = 0

    def _advance(self):
        self._cursor += 1

    def _prompt(self):
        if self._border_drawer is None: 
            self._border_drawer = self.border_drawer_factory.create_border_drawer(self.get_input_surface())

        self._border_drawer.right_prompt(self._cursor, self._cursor_y)
        self._advance()

    # This ignores all cursor state and just plasters the glyphs at the given coord.
    # It will not wrap, scroll, or update any state.
    def print_glyphs_at(self, glyphs: Iterable[U5Glyph], char_coord: Coord):
        target = self.get_input_surface()
        for glyph in glyphs:
            glyph.blit_to_surface(char_coord, target)
            char_coord = char_coord + Vector2(1, 0)

    # This will print at the bottom of the screen and scroll by rolling the component surface upwards.
    # It maintains an x-axis cursor state.
    def print_glyphs(self, glyphs: Iterable[U5Glyph], include_carriage_return: bool = True):

        target = self.get_input_surface()
        for glyph in glyphs:
            if self._cursor >= self.display_config.CONSOLE_SIZE.w:
                self._scroll()
                self._return()
            char_coord = Coord(self._cursor, self._cursor_y)
            glyph.blit_to_surface(char_coord, target)
            self._advance()

        if include_carriage_return:
            self._scroll()
            self._scroll()
            self._return()
            self._prompt()
