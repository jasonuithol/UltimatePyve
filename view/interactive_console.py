from typing import Iterable
from dark_libraries.dark_math import Coord

#from data.global_registry import GlobalRegistry
from models.u5_glyph import U5Glyph
from view.display_config import DisplayConfig
from view.scalable_component import ScalableComponent

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
#    global_registry: GlobalRegistry

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

    def _scroll(self, lines: int = 1):
        self.scroll_dy(self.display_config.FONT_SIZE.h * lines * -1)
    '''
    def print_ascii(self, msg: str|list[int]):
        self.print(msg, "IBM.CH")

    def print_runes(self, msg: str|list[int]):
        self.print(msg, "RUNES.CH")
    '''

    def print_glyphs(self, glyphs: Iterable[U5Glyph]):

        cursor = 0
        target = self.get_input_surface()
        for glyph in glyphs:
            if cursor >= self.display_config.CONSOLE_SIZE.w:
                self._scroll()
                cursor = 0
            char_coord = Coord(cursor, self.display_config.CONSOLE_SIZE.h - 1)
            glyph.blit_to_surface(char_coord, target)
            cursor += 1

        self._scroll()
        self._scroll()

    '''
    def print(self, msg: str|list[int], font_name: str):
        if isinstance(msg, str):
            glyphs: list[U5Glyph] = self.global_registry.font_glyphs.map(map((font_name, ord(char)) for char in msg))
        else:
            glyphs: list[U5Glyph] = list(self.global_registry.font_glyphs.map(map((font_name, glyph_code) for glyph_code in msg)))
        

        print(f"[console] printed msg: {msg}")
    '''
