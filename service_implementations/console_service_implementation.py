from typing import Iterable
from models.u5_glyph import U5Glyph
from services.font_mapper import FontMapper
from view.interactive_console import InteractiveConsole

class ConsoleServiceImplementation:

    # Injectable
    interactive_console: InteractiveConsole
    font_mapper: FontMapper

    def print_ascii(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        if isinstance(msg, str):
            self._print_word_wrapped(msg, FontMapper.IBM_FONT_NAME, include_carriage_return, no_prompt)
        else:
            glyphs = self.font_mapper.map_ascii_codes(msg)
            self.interactive_console.print_glyphs(glyphs, include_carriage_return, no_prompt)

    def print_runes(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        if isinstance(msg, str):
            self._print_word_wrapped(msg, FontMapper.RUNE_FONT_NAME, include_carriage_return, no_prompt)
        else:
            glyphs = self.font_mapper.map_rune_codes(msg)
            self.interactive_console.print_glyphs(glyphs, include_carriage_return, no_prompt)

    def print_glyphs(self, glyphs: Iterable[U5Glyph], include_carriage_return: bool = True, no_prompt = False):
        self.interactive_console.print_glyphs(glyphs, include_carriage_return, no_prompt)

    def backspace(self):
        self.interactive_console.backspace()

    def _print_word_wrapped(self, msg: str, font_name: str, include_carriage_return: bool, no_prompt: bool):
        # Walk the message word-by-word. Before placing a word, scroll+CR if
        # the word wouldn't fit on the rest of the current row (and we aren't
        # already at column 0). Whitespace falling at the end of a row is
        # absorbed so the next row doesn't start with a leading space; a
        # literal '\n' forces a hard CR.
        ic = self.interactive_console
        width = ic.console_width
        i = 0
        while i < len(msg):
            ch = msg[i]
            if ch == "\n":
                ic.print_glyphs([], include_carriage_return=True, no_prompt=True)
                i += 1
                continue
            if ch == " ":
                if ic.cursor_x < width and ic.cursor_x > 0:
                    glyphs = self.font_mapper.map_string(font_name, " ")
                    ic.print_glyphs(glyphs, include_carriage_return=False, no_prompt=True)
                i += 1
                continue
            j = i
            while j < len(msg) and msg[j] not in (" ", "\n"):
                j += 1
            word = msg[i:j]
            if ic.cursor_x > 0 and ic.cursor_x + len(word) > width:
                ic.print_glyphs([], include_carriage_return=True, no_prompt=True)
            glyphs = self.font_mapper.map_string(font_name, word)
            ic.print_glyphs(glyphs, include_carriage_return=False, no_prompt=True)
            i = j
        if include_carriage_return:
            ic.print_glyphs([], include_carriage_return=True, no_prompt=no_prompt)
