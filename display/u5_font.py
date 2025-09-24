from pathlib import Path
from typing import Generator, Iterator
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Size

@immutable
@auto_init
class U5Font:
    data: list[bytearray]
    char_size: Size

    def map_codes(self, msg: list[int]) -> list[bytearray]:
        glyphs: list[bytearray] = []
        for code in msg:
            assert code < len(self.data), f"unmappable code={code} exceeds length of font {len(self.data)})"
            glyphs.append(self.data[code])
        return glyphs

    def map_string(self, msg: str) -> list[bytearray]:
        codes: list[int] = []
        for char in msg:
            ascii_code = ord(char)
            assert ascii_code < len(self.data), f"unmappable character {char} (code={ascii_code} exceeds length of font {len(self.data)})"
            codes.append(ascii_code)
        return self.map_codes(codes)

class U5FontLoader:
    def load(self, name: str, char_size: Size) -> U5Font:
        path = Path(f"u5/{name}")
        ba = path.read_bytes()
        char_length_in_bytes = (char_size.w * char_size.h) // 8
        data = []
        for index in range(len(ba) // char_length_in_bytes):
            data.append(ba[(index * 8):(index * 8) + char_length_in_bytes])

        print(f"[display] Loaded {len(data)} font glyphs from {name}")

        return U5Font(data, char_size)
