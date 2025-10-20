from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.border_glyphs import BorderGlyphs

TOP_LEFT  = 97
TOP_RIGHT = 99
BOT_LEFT  = 100
BOT_RIGHT = 102

TOP  = 98
BOT  = 101
SIDE = 103

class ScrollBorderGlyphFactory(LoggerMixin):

    global_registry: GlobalRegistry

    def load(self):
        self.global_registry.blue_border_glyphs = self._create_border_glyphs()
        self.log("Built blue border glyphs.")

    def _glyph(self, glyph_code: int):
        return self.global_registry.font_glyphs.get("RUNES.CH", glyph_code)

    def _create_border_glyphs(self) -> BorderGlyphs:

        border_glyphs = BorderGlyphs()
        border_glyphs.top_block_glyph    = self._glyph(TOP)
        border_glyphs.bottom_block_glyph = self._glyph(BOT)
        
        border_glyphs.left_block_glyph   = self._glyph(SIDE)
        border_glyphs.right_block_glyph  = self._glyph(SIDE)
        border_glyphs.vertical_block     = self._glyph(SIDE)

        border_glyphs.top_left_cnr_glyph    = self._glyph(TOP_LEFT)
        border_glyphs.top_right_cnr_glyph   = self._glyph(TOP_RIGHT)
        border_glyphs.bottom_left_cnr_glyph = self._glyph(BOT_LEFT)
        border_glyphs.bottom_left_cnr_glyph = self._glyph(BOT_RIGHT)

        return border_glyphs
    