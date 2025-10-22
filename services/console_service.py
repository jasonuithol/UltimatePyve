from typing import Iterable
from services.font_mapper import FontMapper
from view.interactive_console import InteractiveConsole

class ConsoleService:

    # Injectable
    interactive_console: InteractiveConsole
    font_mapper: FontMapper
    
    def print_ascii(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        glyphs = self.font_mapper.map_ascii_message(msg)
        self.interactive_console.print_glyphs(glyphs, include_carriage_return, no_prompt)

    def print_runes(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        glyphs = self.font_mapper.map_rune_message(msg)
        self.interactive_console.print_glyphs(glyphs, include_carriage_return, no_prompt)
