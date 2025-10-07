import pygame

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.u5_glyph import U5Glyph
from view.display_config import DisplayConfig

class U5GlyphLoader(LoggerMixin):

    # Injectable
    display_config: DisplayConfig
    global_registry: GlobalRegistry

    def register_glyphs(self):
        surf = pygame.Surface((1,1))
        white = surf.map_rgb(self.display_config.EGA_PALETTE[15])
        black = surf.map_rgb(self.display_config.EGA_PALETTE[00])
        for font_name, font in self.global_registry.fonts.items():
            for glyph_code, glyph_data in enumerate(font.data):
                glyph = U5Glyph(
                    data = glyph_data,
                    glyph_size = self.display_config.FONT_SIZE,
                    foreground_color_mapped_rgb = white,
                    background_color_mapped_rgb = black
                )
                self.global_registry.font_glyphs.register((font_name, glyph_code), glyph)
                glyph_count = sum(1 for glyph_key in self.global_registry.font_glyphs.keys() if glyph_key[0] == font_name)
            self.log(f"Registered {glyph_count} u5glyphs from {font_name}")
