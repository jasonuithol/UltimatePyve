from typing import Iterable

from data.global_registry import GlobalRegistry
from models.glyph_key import GlyphKey
from models.u5_glyph import U5Glyph

class FontMapper:

    IBM_FONT_NAME = "IBM.CH"
    RUNE_FONT_NAME = "RUNES.CH"

    # Injectable
    global_registry: GlobalRegistry

    def map_code(self, font_name: str, glyph_code: int) -> U5Glyph:
        glyph_key = GlyphKey(font_name, glyph_code)
        result = self.global_registry.font_glyphs.get(glyph_key)
        assert result, f"Could not fetch glyph for font_name={font_name}, glyph_code={glyph_code}, glyph_key={glyph_key}"
        return result

    def map_char(self, font_name: str, char: chr) -> U5Glyph:
        return self.map_code(font_name, ord(char))

    def map_string(self, font_name: str, msg: str) -> list[U5Glyph]:
        if msg is None:
            return None
        return list(map(lambda char: self.map_char(font_name, char), msg))
    
    def map_codes(self, font_name: str, msg: Iterable[int]) -> list[U5Glyph]:
        if msg is None:
            return None
        return list(map(lambda glyph_code: self.map_code(font_name, glyph_code), msg))
    
    def map_ascii_string(self, msg: str) -> list[U5Glyph]:
        return self.map_string(__class__.IBM_FONT_NAME, msg)
    
    def map_rune_string(self, msg: str) -> list[U5Glyph]:
        return self.map_string(__class__.RUNE_FONT_NAME, msg)

    def map_ascii_codes(self, msg: Iterable[int]) -> list[U5Glyph]:
        return self.map_codes(__class__.IBM_FONT_NAME, msg)
    
    def map_rune_codes(self, msg: Iterable[int]) -> list[U5Glyph]:
        return self.map_codes(__class__.RUNE_FONT_NAME, msg)

    def map_ascii_message(self, msg: str | Iterable[int]) -> list[U5Glyph]:
        if isinstance(msg, str):
            return self.map_ascii_string(msg)
        else:
            return self.map_ascii_codes(msg)
    
    def map_rune_message(self, msg: str | Iterable[int]) -> list[U5Glyph]:
        if isinstance(msg, str):
            return self.map_rune_string(msg)
        else:
            return self.map_rune_codes(msg)
