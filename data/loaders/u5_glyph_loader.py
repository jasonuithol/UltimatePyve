import pygame

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.enums.ega_palette_values import EgaPaletteValues
from models.glyph_key import GlyphKey
from models.u5_glyph import U5Glyph
from services.surface_factory import SurfaceFactory
from view.display_config import DisplayConfig

class U5GlyphLoader(LoggerMixin):

    # Injectable
    display_config: DisplayConfig
    global_registry: GlobalRegistry
    surface_factory: SurfaceFactory

    def register_glyphs(self):

        self.foreground = self.global_registry.colors.get(EgaPaletteValues.White)
        self.background = self.global_registry.colors.get(EgaPaletteValues.Black)

        for font_name, font in self.global_registry.fonts.items():
            for glyph_code, glyph_data in enumerate(font.data):

                glyph = self._build_glyph(glyph_data)
                glyph_key = GlyphKey(font_name, glyph_code)
                self.global_registry.font_glyphs.register(glyph_key, glyph)

                glyph_count = sum(1 for glyph_key in self.global_registry.font_glyphs.keys() if glyph_key[0] == font_name)
            self.log(f"Registered {glyph_count} u5glyphs from {font_name}")

    def _build_glyph(self, data: bytearray) -> U5Glyph:

        surf = self.surface_factory.create_surface(self.display_config.FONT_SIZE)

        target = pygame.PixelArray(surf)
        for y in range(self.display_config.FONT_SIZE.h):
            for x in range(self.display_config.FONT_SIZE.w):
                bit_index = x + (y * self.display_config.FONT_SIZE.w)
                byte_index = bit_index // 8
                bit_offset = bit_index % 8
                bit_value = data[byte_index] & (1 << (7 - bit_offset))
                target[x, y] = self.foreground if bit_value else self.background        
        del target

        return U5Glyph(surf)

