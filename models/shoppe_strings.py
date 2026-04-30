"""
SHOPPE.DAT decoder.

Format (verified empirically against canonical U5 lines):
- Stream of NUL-terminated strings.
- Bytes < 0x80     = literal ASCII characters.
- Bytes >= 0x80    = compressed-word reference. Subtract 0x7F to get the
                     TLK-style byte value, then look up via _COMPRESSED_LOOKUP
                     (the same table TLK uses; it has gaps for NUL and command
                     bytes, so a flat subtraction will not work). The result is
                     an index into the compressed-word dictionary stored at
                     DATA.OVL 0x104c..0x129a.

Strings include U5 placeholder characters that the controller resolves at
display time:
    %  price
    &  item name
    $  shopkeeper name
    #  town name
    @  good morning/afternoon/evening
"""

from pathlib import Path

from models.data_ovl import DataOVL
from models.tlk_file import _COMPRESSED_LOOKUP


class ShoppeStrings:

    def __init__(self, strings: list[str]):
        self._strings = strings

    @classmethod
    def from_path(cls, u5_path: Path, data_ovl: DataOVL) -> "ShoppeStrings":
        raw = (u5_path / "SHOPPE.DAT").read_bytes()
        words = [b.decode("ascii", errors="replace")
                 for b in data_ovl.compressed_words.split(b"\x00")]
        return cls(_decode(raw, words))

    def __len__(self) -> int:
        return len(self._strings)

    def __getitem__(self, index: int) -> str:
        return self._strings[index]

    def all(self) -> list[str]:
        return list(self._strings)


def _decode(raw: bytes, words: list[str]) -> list[str]:
    decoded: list[str] = []
    current: list[str] = []
    for byte in raw:
        if byte == 0x00:
            decoded.append(_tidy("".join(current)))
            current = []
            continue
        if byte < 0x80:
            current.append(chr(byte))
        else:
            idx = _COMPRESSED_LOOKUP.get(byte - 0x7F)
            if idx is not None and 0 <= idx < len(words):
                current.append(" ")
                current.append(words[idx])
                current.append(" ")
            else:
                current.append(f"<{byte:02X}>")
    if current:
        decoded.append(_tidy("".join(current)))
    return decoded


def _tidy(text: str) -> str:
    while "  " in text:
        text = text.replace("  ", " ")
    for p in (",", ".", ";", ":", "!", "?"):
        text = text.replace(f" {p}", p)
    return text.strip()
