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
the boundary between the keyword Q&A section and the label/goto section;
the label section holds jump targets addressable by raw label bytes
(0x91..0x9B) appearing elsewhere in the script.

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
from typing import Literal

from models.enums.inventory_offset import InventoryOffset


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


def is_label_byte(b: int) -> bool:
    return _MIN_LABEL <= b <= _MAX_LABEL


def label_byte_to_num(b: int) -> int:
    return b - _MIN_LABEL


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


class ChangeItemCode(IntEnum):
    """
    CHANGE (0x86) operand bytes — observed values used by Ultima V NPCs.

    TALK.OVL dispatches on the operand at file offset 0x0682. Three behaviours:
      operand < 0x40            : items[operand] += 1, capped at 99
                                  (items array starts at SAVED.GAM 0x21A)
      operand in {0x41, 0x42}   : u16 slot += 1, capped at 9999  (FOOD, GOLD)
      operand in {0x43..0x47, 0x4B} : u8 slot += 1, capped at 99
      operand in {0x48..0x4A}   : u8 slot := 0xFF  (boolean quest-item flags)
    """
    # Items array branch (operand < 0x40)
    JEWELLED_SHIELD = 0x08  # Thrud (KEEP.TLK npc#8)
    CROSSBOW        = 0x1C  # Thrud (KEEP.TLK npc#8)
    # Special slots
    FOOD            = 0x41
    GOLD            = 0x42
    KEYS            = 0x43
    GEMS            = 0x44
    TORCHES         = 0x45
    GRAPPLE         = 0x46
    MAGIC_CARPETS   = 0x47
    SEXTANTS        = 0x48
    SPY_GLASSES     = 0x49
    BLACK_BADGE     = 0x4A
    SKULL_KEYS      = 0x4B


_CHANGE_SPECIAL_TO_INVENTORY: dict[int, InventoryOffset] = {
    ChangeItemCode.FOOD:          InventoryOffset.FOOD,
    ChangeItemCode.GOLD:          InventoryOffset.GOLD,
    ChangeItemCode.KEYS:          InventoryOffset.KEYS,
    ChangeItemCode.GEMS:          InventoryOffset.GEMS,
    ChangeItemCode.TORCHES:       InventoryOffset.TORCHES,
    ChangeItemCode.GRAPPLE:       InventoryOffset.GRAPPLE,
    ChangeItemCode.MAGIC_CARPETS: InventoryOffset.MAGIC_CARPETS,
    ChangeItemCode.SEXTANTS:      InventoryOffset.SEXTANTS,
    ChangeItemCode.SPY_GLASSES:   InventoryOffset.SPY_GLASSES,
    ChangeItemCode.BLACK_BADGE:   InventoryOffset.BLACK_BADGE,
    ChangeItemCode.SKULL_KEYS:    InventoryOffset.SKULL_KEYS,
}

_CHANGE_FLAG_OPERANDS = frozenset({
    ChangeItemCode.SEXTANTS,
    ChangeItemCode.SPY_GLASSES,
    ChangeItemCode.BLACK_BADGE,
})

ChangeKind = Literal["add", "set_flag"]


def change_operand_to_inventory(operand: int) -> InventoryOffset | None:
    """
    Map a CHANGE operand byte to its target SAVED.GAM inventory slot.
    Returns None for operands outside the ranges TALK.OVL handles
    (>= 0x40 and not in 0x41..0x4B).
    """
    if 0 <= operand < 0x40:
        offset = 0x21A + operand
        try:
            return InventoryOffset(offset)
        except ValueError:
            return None
    return _CHANGE_SPECIAL_TO_INVENTORY.get(operand)


def change_operand_kind(operand: int) -> ChangeKind | None:
    """
    Whether the CHANGE handler increments a counter or sets a 0xFF flag.
    """
    if change_operand_to_inventory(operand) is None:
        return None
    return "set_flag" if operand in _CHANGE_FLAG_OPERANDS else "add"


_OPERAND_COMMANDS = frozenset({TalkCommand.CHANGE, TalkCommand.DEFINE_LABEL})


@dataclass
class ScriptItem:
    command: int  # TalkCommand value, or raw byte for labels (0x91..0x9B)
    text: str = ""
    operand: int | None = None  # 1-byte operand for CHANGE / DEFINE_LABEL

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

    def contains_command(self, command: int) -> bool:
        return any(it.command == command for it in self.items)

    def split_into_sections(self) -> list[list[ScriptItem]]:
        """
        Split the item stream into sections, mirroring Ultima5Redux's
        TalkScript.ScriptLine.SplitIntoSections(). Sections are the unit
        over which the IF_ELSE_KNOWS_NAME skip-instructions operate.

        A START_NEW_SECTION (0xA2) opens a fresh section. IF_ELSE_KNOWS_NAME
        and DO_NOTHING_SECTION each occupy their own "stump" section, then
        the item after them forces another split.
        """
        sections: list[list[ScriptItem]] = [[]]
        n = 0
        first = True
        force_split_next = False
        for item in self.items:
            cmd = item.command
            if cmd == TalkCommand.START_NEW_SECTION:
                n += 1
                sections.append([])
                continue
            if cmd in (TalkCommand.IF_ELSE_KNOWS_NAME, TalkCommand.DO_NOTHING_SECTION):
                n += 1
                sections.append([])
                sections[n].append(item)
                force_split_next = True
                continue
            if first:
                n = 0
            if force_split_next:
                force_split_next = False
                n += 1
                sections.append([])
            sections[n].append(item)
            first = False
        return sections


@dataclass
class TlkLabel:
    """
    A parsed label region from a TLK script. Mirrors Ultima5Redux's
    ScriptTalkLabel.

    `initial_line` is the label-definition line itself — it begins with the
    [START_LABEL_DEFINITION, label_byte] marker, but typically has the
    label's entry text (often a yes/no question) immediately after those
    two marker items. Rendering drops the two markers as a no-op and emits
    the remaining items.

    `default_answers` is a list of fallback lines shown when the user's
    follow-up keyword doesn't match anything in `keyword_responses`.
    Ultima V uses this pattern extensively: the NPC asks a question via
    initial_line; a keyword match branches to a specific response;
    otherwise the default_answers are spoken.
    """
    label_num:         int
    initial_line:      ScriptLine             = field(default_factory=ScriptLine)
    default_answers:   list[ScriptLine]       = field(default_factory=list)
    keyword_responses: dict[str, ScriptLine]  = field(default_factory=dict)


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
    labels:            dict[int, TlkLabel]   = field(default_factory=dict)
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

    i = 0
    while i < len(raw):
        byte = raw[i]
        if byte == 0x00:
            # End of line. Bradhannah appends "\n" here, but we trim trailing
            # whitespace at the line boundary for cleaner Python semantics.
            flush_buffer()
            lines.append(current)
            current = ScriptLine()
            writing_chars = False
            i += 1
            continue

        if _is_char_byte(byte):
            ch = chr(byte - 0x80)
            if ch == "@":
                # Bradhannah skips '@' entirely — it ends a prompt run.
                i += 1
                continue
            buffer += ch
            writing_chars = True
            i += 1
            continue

        # Not a character byte — either a compressed word or a command.
        if writing_chars:
            # Moving from chars to lookup: insert a separating space.
            buffer += " "
            writing_chars = False

        if words.has(byte):
            buffer += words.get(byte) + " "
            i += 1
            continue

        # Command byte (or label in 0x91..0x9B range).
        flush_buffer()
        if byte in _OPERAND_COMMANDS and i + 1 < len(raw):
            # Two-byte command — TALK.OVL stores the command at memory
            # [0x4AEE] then re-enters the parser to read the operand byte.
            current.items.append(ScriptItem(byte, operand=raw[i + 1]))
            i += 2
            continue
        if byte == TalkCommand.GOLD and i + 3 < len(raw):
            # Four-byte command: GOLD opcode + three high-bit ASCII digits
            # encoding the price (e.g. <0x85><0xB0><0xB0><0xB3> = 003).
            digits = "".join(chr(raw[i + k] - 0x80) for k in (1, 2, 3))
            try:
                price = int(digits)
            except ValueError:
                price = None
            current.items.append(ScriptItem(byte, operand=price))
            i += 4
            continue
        current.items.append(ScriptItem(byte))
        i += 1

    # Trailing bytes without a closing NUL still form a line.
    flush_buffer()
    if current.items:
        lines.append(current)

    return lines


def _is_end_of_label_section(line: ScriptLine) -> bool:
    # Redux: [StartLabelDefinition, EndScript] == terminator of the label region.
    if len(line.items) < 2:
        return False
    return (
        line.items[0].command == TalkCommand.START_LABEL_DEFINITION
        and line.items[1].command == TalkCommand.END_SCRIPT
    )


def _is_label_definition(line: ScriptLine) -> bool:
    # Redux: [StartLabelDefinition, <label byte>] — the opener for a new label.
    if len(line.items) < 2:
        return False
    if line.items[0].command != TalkCommand.START_LABEL_DEFINITION:
        return False
    return is_label_byte(line.items[1].command)


def _extract_qa_section(
    lines: list[ScriptLine],
    start: int,
    stop_at_label_definition: bool,
) -> tuple[dict[str, ScriptLine], int]:
    """
    Walk (keyword)->(response) pairs starting at `start`. Returns the
    collected responses and the index of the first line NOT consumed
    (either a START_LABEL_DEFINITION line, or past the end of `lines`).
    Handles OR-chained keyword alternatives.
    """
    responses: dict[str, ScriptLine] = {}
    i = start
    while i + 1 < len(lines):
        line = lines[i]
        first = line.first_item()
        if first is None:
            i += 1
            continue
        if stop_at_label_definition and first.command == TalkCommand.START_LABEL_DEFINITION:
            break

        keywords: list[str] = []
        keyword_text = line.as_text().lower()
        if keyword_text:
            keywords.append(keyword_text)

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

    return responses, i


def _extract_labels(lines: list[ScriptLine], start: int) -> dict[int, TlkLabel]:
    """
    Parse the label section that begins at `start` (which must point at a
    START_LABEL_DEFINITION line, or the end of `lines`). Mirrors
    Ultima5Redux's ScriptTalkLabel parsing in TalkScript.InitScript.
    """
    labels: dict[int, TlkLabel] = {}
    i = start
    while i < len(lines):
        line = lines[i]
        if _is_end_of_label_section(line):
            break
        if not _is_label_definition(line):
            # Malformed / defensive: give up so we don't crash on bad data.
            break

        label_num = label_byte_to_num(line.items[1].command)
        label = TlkLabel(label_num=label_num, initial_line=line)
        labels[label_num] = label
        i += 1

        # First default answer (entry text) — present unless the next line is
        # already another label definition (empty label).
        if i < len(lines) and not _is_label_definition(lines[i]) and not _is_end_of_label_section(lines[i]):
            label.default_answers.append(lines[i])
            i += 1
        else:
            continue

        # Label-scoped Q&A and additional default answers. A line that reads
        # as a question keyword (short, no spaces) is treated as a Q keyword;
        # otherwise it's appended as another default answer.
        while i < len(lines):
            if _is_label_definition(lines[i]) or _is_end_of_label_section(lines[i]):
                break

            current = lines[i]
            text = current.as_text().lower()
            looks_like_keyword = bool(text) and " " not in text and 1 <= len(text) <= 6

            if looks_like_keyword and i + 1 < len(lines):
                # Gather OR-chained keywords just like the pre-label loop.
                keywords = [text]
                while i + 2 < len(lines):
                    nxt = lines[i + 1]
                    nxt_first = nxt.first_item()
                    if nxt_first is None or nxt_first.command != TalkCommand.OR:
                        break
                    i += 2
                    alt_text = lines[i].as_text().lower()
                    if alt_text:
                        keywords.append(alt_text)
                answer = lines[i + 1]
                for kw in keywords:
                    label.keyword_responses.setdefault(kw, answer)
                i += 2
            else:
                # Non-keyword line inside the label body: another default answer.
                label.default_answers.append(current)
                i += 1

    return labels


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

            responses, label_section_start = _extract_qa_section(
                lines, start=5, stop_at_label_definition=True
            )
            labels = _extract_labels(lines, start=label_section_start)
            dialog = NpcDialog(
                npc_dialog_number = npc_index,
                name              = lines[0],
                description       = lines[1],
                greeting          = lines[2],
                job               = lines[3],
                bye               = lines[4],
                keyword_responses = responses,
                labels            = labels,
                script_lines      = lines,
            )
            self.dialogs[npc_index] = dialog
