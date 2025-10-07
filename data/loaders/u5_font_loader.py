from pathlib import Path

from dark_libraries.dark_math import Size

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.u5_font import U5Font

class U5FontLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def load(self, name: str, char_size: Size) -> U5Font:
        path = Path(f"u5/{name}")
        ba = path.read_bytes()
        char_length_in_bytes = (char_size.w * char_size.h) // 8
        data = []
        for index in range(len(ba) // char_length_in_bytes):
            data.append(ba[(index * 8):(index * 8) + char_length_in_bytes])

        self.log(f"Loaded {len(data)} font data blobs from {name}")

        return U5Font(data, char_size)
    
    def register_fonts(self):
        for font_name in ["IBM.CH", "RUNES.CH"]:
            font = self.load(font_name, Size(8,8))
            self.global_registry.fonts.register(font_name, font)