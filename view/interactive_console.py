from typing import Iterable
from dark_libraries.dark_math import Coord, Vector2

from data.global_registry import GlobalRegistry
from models.glyph_key import GlyphKey
from models.sprite import Sprite
from models.u5_glyph import U5Glyph

from .scalable_component import ScalableComponent
from .display_config     import DisplayConfig
from .border_drawer      import BorderDrawer

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
    global_registry: GlobalRegistry

    def __init__(self):
        self._cursor_x: int = 0
        self._border_drawer: BorderDrawer = None

    def _after_inject(self):
        super().__init__(self.display_config.CONSOLE_SIZE * self.display_config.FONT_SIZE, self.display_config.SCALE_FACTOR)
        super()._after_inject()
        self._cursor_y = self.display_config.CONSOLE_SIZE.h - 1

    def init(self):
        self._cursor_sprite = Sprite[U5Glyph](
            frames = [
                self.global_registry.font_glyphs.get(GlyphKey("IBM.CH", glyph_code))
                for glyph_code in [5,6,7,8]
            ],
            frame_duration_seconds = 0.125
        )
        self._blank_glyph = self.global_registry.font_glyphs.get(GlyphKey("IBM.CH", 0))

    # This will print at the bottom of the screen and scroll by rolling the component surface upwards.
    # It maintains an x-axis cursor state.
    def print_glyphs(self, glyphs: Iterable[U5Glyph], include_carriage_return: bool = True, no_prompt = False):

        target = self.get_input_surface()
        for glyph in glyphs:
            if self._cursor_x >= self.display_config.CONSOLE_SIZE.w:
                self._scroll()
                self._return()
            char_coord = Coord[int](self._cursor_x, self._cursor_y)
            glyph.blit_to_surface(char_coord, target)
            self._advance()

        if include_carriage_return:
            self._scroll()
            self._return()

            if not no_prompt:
                self._scroll()
                self._prompt()

    def _scroll(self, lines: int = 1):
        self._erase_cursor()
        self.scroll_dy(self.display_config.FONT_SIZE.h * lines * -1)

    def _return(self):
        self._cursor_x = 0

    def _advance(self):
        self._cursor_x += 1

    def _prompt(self):
        if self._border_drawer is None: 
            self._border_drawer = BorderDrawer(self.global_registry.blue_border_glyphs, self.get_input_surface())

        self._border_drawer.right_prompt(self._cursor_x, self._cursor_y)
        self._advance()

    def _erase_cursor(self):
        target = self.get_input_surface()
        coord = Coord[int](self._cursor_x, self._cursor_y)
        self._blank_glyph.blit_to_surface(coord, target)

    def _draw_cursor(self):
        target = self.get_input_surface()
        coord = Coord[int](self._cursor_x, self._cursor_y)
        current_frame: U5Glyph = self._cursor_sprite.get_current_frame(0.0)
        current_frame.blit_to_surface(coord, target)

    def draw(self):
        #
        # NOTE: We preserve whatever already exists on the input surface, apart from animating the cursor
        #
        self._erase_cursor()
        self._draw_cursor()
