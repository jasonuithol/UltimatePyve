"""
Ultima V TLK file parser.

TLK file layout (TOWNE.TLK / CASTLE.TLK / KEEP.TLK / DWELLING.TLK):
    u16 LE  n_entries
    n_entries * (u16 LE npc_index, u16 LE file_offset)
    ... variable-length script blocks at those offsets.

Each script block is a stream of bytes split into "script lines" by NUL (0x00).
The first five lines are fixed: Name, Description, Greeting, Job, Bye.
Subsequent line pairs are (keyword, response), optionally chained via the Or
command for multi-keyword alternatives. A StartLabelDefinition (0x90) marks
the boundary between the keyword Q&A section and the label/goto section,
which we currently skip.

Byte decoding (per Bradhannah's Ultima5Redux CompressedWordReference and
TalkScripts, simplified):

  0x00                        end-of-line
  0xA0..0xA1, 0xA5..0xDA,
  0xE1..0xFA                  plain character; emit chr(byte - 0x80)
  1..7, 9..27, 29..49, 51..64,
  66, 68..69, 71, 76..129     compressed word; look up in DATA.OVL dictionary
  0x7E..0x9F, 0xA2,
  0xFD..0xFF                  talk-script command byte (see TalkCommand)
  0x91..0x9B                  label id (embedded in the command stream)
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path


class TalkCommand(IntEnum):
    PLAIN_STRING                        = 0x00
    USER_INPUT_NOT_RECOGNIZED           = 0x7E
    PROMPT_USER_FOR_INPUT_USER_INTEREST = 0x7F
    PROMPT_USER_FOR_INPUT_NPC_QUESTION  = 0x80
    AVATARS_NAME                        = 0x81
    END_CONVERSATION                    = 0x82
    PAUSE                               = 0x83
    JOIN_PARTY                          = 0x84
    GOLD                                = 0x85
    CHANGE                              = 0x86
    OR                                  = 0x87
    ASK_NAME                            = 0x88
    KARMA_PLUS_ONE                      = 0x89
    KARMA_MINUS_ONE                     = 0x8A
    CALL_GUARDS                         = 0x8B
    IF_ELSE_KNOWS_NAME                  = 0x8C
    NEW_LINE                            = 0x8D
    RUNE                                = 0x8E
    KEY_WAIT                            = 0x8F
    START_LABEL_DEFINITION              = 0x90
    # 0x91..0x9B are label ids (MIN_LABEL..MAX_LABEL).
    END_SCRIPT                          = 0x9F
    START_NEW_SECTION                   = 0xA2
    GOTO_LABEL                          = 0xFD
    DEFINE_LABEL                        = 0xFE
    DO_NOTHING_SECTION                  = 0xFF


_MIN_LABEL = 0x91
_MAX_LABEL = 0x9B
_TOTAL_LABELS = _MAX_LABEL - _MIN_LABEL + 1  # 11 (C# says 10; not load-bearing)


def _is_char_byte(b: int) -> bool:
    return b in (0xA0, 0xA1) or 0xA5 <= b <= 0xDA or 0xE1 <= b <= 0xFA


def _build_compressed_lookup() -> dict[int, int]:
    """
    Map from TLK byte value to index into the DATA.OVL compressed-word list.
    Mirrors the Bradhannah table (index gaps and all).
    """
    lookup: dict[int, int] = {}
    offset = 0

    def add(start: int, stop: int, off: int):
        for i in range(start, stop + 1):
            lookup[i] = i + off

    offset -= 1; add(1, 7, offset)
    offset -= 1; add(9, 27, offset)
    offset -= 1; add(29, 49, offset)
    offset -= 1; add(51, 64, offset)
    offset -= 1; add(66, 66, offset)
    offset -= 1; add(68, 69, offset)
    offset -= 1; add(71, 71, offset)
    offset -= 4
    add(76, 129, offset)
    return lookup


_COMPRESSED_LOOKUP = _build_compressed_lookup()


class CompressedWords:
    """
    Lookup table for the compressed words in DATA.OVL. NUL-separated string
    list at DATA.OVL 0x104c..0x129a.
    """

    def __init__(self, chunk: bytes):
        raw_strs = chunk.split(b"\x00")
        self._words: list[str] = [s.decode("ascii", errors="replace") for s in raw_strs]

    def has(self, byte_value: int) -> bool:
        idx = _COMPRESSED_LOOKUP.get(byte_value)
        return idx is not None and 0 <= idx < len(self._words) and self._words[idx] != ""

    def get(self, byte_value: int) -> str:
        idx = _COMPRESSED_LOOKUP[byte_value]
        return self._words[idx]


@dataclass
class ScriptItem:
    command: int  # TalkCommand value, or raw byte for labels (0x91..0x9B)
    text: str = ""

    @property
    def is_plain_string(self) -> bool:
        return self.command == TalkCommand.PLAIN_STRING


@dataclass
class ScriptLine:
    items: list[ScriptItem] = field(default_factory=list)

    def as_text(self) -> str:
        return "".join(it.text for it in self.items if it.is_plain_string).strip()

    def first_item(self) -> ScriptItem | None:
        return self.items[0] if self.items else None


@dataclass
class NpcDialog:
    """
    A parsed TLK script for one NPC.

    The five canonical lines are mandatory. keyword_responses maps the raw
    keyword text (as spoken by the Avatar, lowercase, up to 4 chars typically)
    to the NPC's response line.
    """
    npc_dialog_number: int  # 1-based index as stored in NPC file dialog_numbers
    name:        ScriptLine
    description: ScriptLine
    greeting:    ScriptLine
    job:         ScriptLine
    bye:         ScriptLine
    keyword_responses: dict[str, ScriptLine] = field(default_factory=dict)
    script_lines:      list[ScriptLine]      = field(default_factory=list)


def _decode_script_block(raw: bytes, words: CompressedWords) -> list[ScriptLine]:
    """
    Decode a single NPC's byte block into a list of ScriptLines.

    Each line is a list of ScriptItems. Plain text runs are coalesced into
    PLAIN_STRING items with whitespace inserted around compressed-word
    lookups (matching the original rendering).
    """
    lines: list[ScriptLine] = []
    current = ScriptLine()
    buffer = ""
    writing_chars = False  # tracks single-char mode for space insertion

    def flush_buffer():
        nonlocal buffer
        if buffer:
            current.items.append(ScriptItem(TalkCommand.PLAIN_STRING, buffer))
            buffer = ""

    for byte in raw:
        if byte == 0x00:
            # End of line. Bradhannah appends "\n" here, but we trim trailing
            # whitespace at the line boundary for cleaner Python semantics.
            flush_buffer()
            lines.append(current)
            current = ScriptLine()
            writing_chars = False
            continue

        if _is_char_byte(byte):
            ch = chr(byte - 0x80)
            if ch == "@":
                # Bradhannah skips '@' entirely — it ends a prompt run.
                continue
            buffer += ch
            writing_chars = True
            continue

        # Not a character byte — either a compressed word or a command.
        if writing_chars:
            # Moving from chars to lookup: insert a separating space.
            buffer += " "
            writing_chars = False

        if words.has(byte):
            buffer += words.get(byte) + " "
            continue

        # Command byte (or label in 0x91..0x9B range).
        flush_buffer()
        current.items.append(ScriptItem(byte))

    # Trailing bytes without a closing NUL still form a line.
    flush_buffer()
    if current.items:
        lines.append(current)

    return lines


def _extract_keyword_responses(lines: list[ScriptLine]) -> dict[str, ScriptLine]:
    """
    Walk the script lines after the fixed five, collecting
    (keyword) -> (response) pairs. Stops at the label section marker
    (START_LABEL_DEFINITION). Handles the OR command for multi-keyword
    alternatives.
    """
    responses: dict[str, ScriptLine] = {}
    i = 5
    while i + 1 < len(lines):
        line = lines[i]
        first = line.first_item()
        if first is None:
            i += 1
            continue
        if first.command == TalkCommand.START_LABEL_DEFINITION:
            break

        # Gather keyword(s) for this Q&A pair.
        keywords: list[str] = []
        keyword_text = line.as_text().lower()
        if keyword_text:
            keywords.append(keyword_text)

        # If the next line begins with OR, it chains another keyword.
        while i + 2 < len(lines):
            next_line = lines[i + 1]
            next_first = next_line.first_item()
            if next_first is None or next_first.command != TalkCommand.OR:
                break
            i += 2
            alt_text = lines[i].as_text().lower()
            if alt_text:
                keywords.append(alt_text)

        response = lines[i + 1] if i + 1 < len(lines) else ScriptLine()
        for kw in keywords:
            responses.setdefault(kw, response)
        i += 2

    return responses


class TlkFile:
    """
    Parses an Ultima V .TLK file into a dict of NpcDialog keyed by the TLK
    npc index (which matches the dialog_numbers field in the .NPC file).
    """

    def __init__(self, path: Path, compressed_words: CompressedWords):
        raw = Path(path).read_bytes()
        n_entries = int.from_bytes(raw[0:2], "little")

        # Header rows, 4 bytes each.
        offsets: list[tuple[int, int]] = []  # (npc_index, file_offset)
        for i in range(n_entries):
            hdr = 2 + i * 4
            npc_index = int.from_bytes(raw[hdr:hdr + 2], "little")
            file_offset = int.from_bytes(raw[hdr + 2:hdr + 4], "little")
            offsets.append((npc_index, file_offset))

        # Slice each NPC's chunk out of the file.
        self.dialogs: dict[int, NpcDialog] = {}
        for entry_i, (npc_index, start) in enumerate(offsets):
            if entry_i + 1 < len(offsets):
                end = offsets[entry_i + 1][1]
            else:
                end = len(raw)
            chunk = raw[start:end]
            lines = _decode_script_block(chunk, compressed_words)

            # Pad up to 5 canonical lines so malformed entries don't crash us.
            while len(lines) < 5:
                lines.append(ScriptLine())

            dialog = NpcDialog(
                npc_dialog_number = npc_index,
                name              = lines[0],
                description       = lines[1],
                greeting          = lines[2],
                job               = lines[3],
                bye               = lines[4],
                keyword_responses = _extract_keyword_responses(lines),
                script_lines      = lines,
            )
            self.dialogs[npc_index] = dialog
