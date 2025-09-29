import pygame

from dark_libraries.dark_math import Coord, Size
from display.display_config import DisplayConfig
from display.scalable_component import ScalableComponent
from display.u5_font import U5Font, U5FontRegistry, U5Glyph

CHAR_SIZE_PIXELS = Size(8,8)
CONSOLE_SIZE_IN_CHARS = Size(32, 13)

class InteractiveConsole(ScalableComponent):

    # Injectable
    display_config: DisplayConfig
    u5_font_registry: U5FontRegistry

    def __init__(self):
        pass

    def _after_inject(self):
        super().__init__(
            unscaled_size_in_pixels = self.display_config.CONSOLE_SIZE.scale(self.display_config.FONT_SIZE),
            scale_factor            = self.display_config.SCALE_FACTOR
        )

        # TODO: Get these from ega-palette
        self._font_color = self._scaled_surface.map_rgb((255,255,255))
        self._prompt_color = self._scaled_surface.map_rgb((0,255,0))

    def _scroll(self, lines: int = 1):
        self.scroll_dy(CHAR_SIZE_PIXELS.h * lines * -1)

    def draw_glyph(self, char_coord: Coord, glyph_data: bytearray, target: pygame.Surface):
        glyph = U5Glyph(
            data                        = glyph_data,
            glyph_size                  = CHAR_SIZE_PIXELS,
            foreground_color_mapped_rgb = self._font_color,
            background_color_mapped_rgb = self._back_color
        )
        glyph.blit_to_surface(char_coord, target)

    def print_ascii(self, msg: str|list[int]):
        self.print(msg, self.u5_font_registry.get_font("IBM.CH"))

    def print_rune(self, msg: str|list[int]):
        self.print(msg, self.u5_font_registry.get_font("RUNES.CH"))

    def print(self, msg: str|list[int], font: U5Font):
        if isinstance(msg, str):
            glyphs = font.map_string(msg)
        else:
            glyphs = font.map_codes(msg)
        cursor = 0
        
        for glyph_index in range(len(glyphs)):
            if cursor >= CONSOLE_SIZE_IN_CHARS.w:
                self._scroll()
                cursor = 0
            char_coord = Coord(cursor, CONSOLE_SIZE_IN_CHARS.h - 1)
            self.draw_glyph(char_coord, glyphs[glyph_index], self.get_input_surface())
            cursor += 1

        self._scroll()
        self._scroll()

        print(f"[console] printed msg: {msg}")
