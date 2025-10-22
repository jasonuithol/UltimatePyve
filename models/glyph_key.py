class GlyphKey(tuple[str,int]):

    # NOTE: This does NOT get inherited !
    __slots__ = ()

    def __new__(cls, font_name: str, glyph_code: int):
        return super().__new__(cls, (font_name, glyph_code))

    @property
    def font_name(self)  -> str: 
        return self[0]

    @property
    def glyph_code(self) -> int: 
        return self[1]

