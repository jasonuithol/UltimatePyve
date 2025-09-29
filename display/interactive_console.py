from dark_libraries.dark_math import Coord, Size
from display.display_config import DisplayConfig
from display.scalable_component import ScalableComponent
from display.u5_font import U5Glyph, U5GlyphRegistry

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
    u5_glyph_registry: U5GlyphRegistry

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

    def _scroll(self, lines: int = 1):
        self.scroll_dy(self.display_config.FONT_SIZE.h * lines * -1)

    def print_ascii(self, msg: str|list[int]):
        self.print(msg, "IBM.CH")

    def print_rune(self, msg: str|list[int]):
        self.print(msg, "RUNES.CH")

    def print(self, msg: str|list[int], font_name: str):
        if isinstance(msg, str):
            glyphs: list[U5Glyph] = self.u5_glyph_registry.map_string_to_glyphs(font_name = font_name, message = msg)
        else:
            glyphs: list[U5Glyph] = self.u5_glyph_registry.map_codes_to_glyphs(font_name = font_name, glyph_codes = msg)
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

        print(f"[console] printed msg: {msg}")
