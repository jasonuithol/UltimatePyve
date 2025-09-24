import pygame

from dark_libraries.custom_decorators import auto_init
from dark_libraries.dark_math import Coord, Size
from display.u5_font import U5Font

CHAR_SIZE_PIXELS = Size(8,8)
CONSOLE_SIZE_IN_CHARS = Size(32, 13)

@auto_init
class InteractiveConsole:

    ascii_font: U5Font
    rune_font: U5Font

    _unscaled_size: Size = Size(CHAR_SIZE_PIXELS.w * CONSOLE_SIZE_IN_CHARS.w, CHAR_SIZE_PIXELS.h * CONSOLE_SIZE_IN_CHARS.h)
    _display_scale: int = 2

    def _after_inject(self):
        self._scaled_surface: pygame.Surface = pygame.Surface(self.view_size_in_pixels_scaled().to_tuple())
        self._unscaled_surface: pygame.Surface = pygame.Surface(self.view_size_in_pixels_unscaled().to_tuple())

        self._font_color = self._scaled_surface.map_rgb((255,255,255))
        self._prompt_color = self._scaled_surface.map_rgb((0,255,0))
        self._back_color = self._scaled_surface.map_rgb((0,0,0))

        self._scaled_surface.fill(self._back_color)
        self._scroll_fill_rect = (
            0, 
            CHAR_SIZE_PIXELS.h * (CONSOLE_SIZE_IN_CHARS.h - 1),
            self._unscaled_size.w,
            CHAR_SIZE_PIXELS.h
        )

    def view_size_in_pixels_unscaled(self) -> Size:
        return self._unscaled_size

    def view_size_in_pixels_scaled(self) -> Size:
        return self._unscaled_size.scale(self._display_scale)

    def get_input_surface(self) -> pygame.Surface:
        return self._unscaled_surface

    def get_output_surface(self) -> pygame.Surface:

        pygame.transform.scale(
            surface      = self._unscaled_surface,
            size         = self.view_size_in_pixels_scaled().to_tuple(),
            dest_surface = self._scaled_surface
        )

        return self._scaled_surface
    
    def _scroll(self, lines: int = 1):
        surf = self.get_input_surface()
        surf.scroll(0, CHAR_SIZE_PIXELS.h * lines * -1)
        surf.fill(self._back_color, self._scroll_fill_rect)

    def draw_glyph(self, char_coord: Coord, glyph: bytearray, target: pygame.PixelArray):
        origin_x, origin_y = char_coord.x * CHAR_SIZE_PIXELS.w, char_coord.y * CHAR_SIZE_PIXELS.h

        for y in range(CHAR_SIZE_PIXELS.h):
            for x in range(CHAR_SIZE_PIXELS.w):
                bit_index = x + (y * CHAR_SIZE_PIXELS.h)
                byte_index = bit_index // 8
                bit_offset = bit_index % 8
                bit_value = glyph[byte_index] & (1 << (8 - bit_offset))
                target[x + origin_x, y + origin_y] = self._font_color if bit_value else self._back_color

    def print_ascii(self, msg: str|list[int]):
        self.print(msg, self.ascii_font)

    def print_rune(self, msg: str|list[int]):
        self.print(msg, self.rune_font)

    def print(self, msg: str|list[int], font: U5Font):
        if isinstance(msg, str):
            glyphs = font.map_string(msg)
        else:
            glyphs = font.map_codes(msg)
        cursor = 0

        pa = pygame.PixelArray(self.get_input_surface())
        
        for glyph_index in range(len(glyphs)):
            if cursor >= CONSOLE_SIZE_IN_CHARS.w:
                self._scroll()
                cursor = 0
            char_coord = Coord(cursor, CONSOLE_SIZE_IN_CHARS.h - 1)
            self.draw_glyph(char_coord, glyphs[glyph_index], pa)
            cursor += 1

        del pa

        self._scroll()
        self._scroll()

        print(f"[console] printed msg: {msg}")
