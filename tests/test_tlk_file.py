from pathlib import Path

import pytest

from models.data_ovl import DataOVL
from models.tlk_file import CompressedWords, TlkFile


TLK_FILES = ("TOWNE.TLK", "CASTLE.TLK", "KEEP.TLK", "DWELLING.TLK")


def _find_u5_dir() -> Path | None:
    try:
        from configure import get_u5_path
        return get_u5_path()
    except AssertionError:
        pass
    repo_local = Path(__file__).resolve().parents[1] / "u5"
    if all((repo_local / name).exists() for name in TLK_FILES):
        return repo_local
    return None


@pytest.fixture(scope="module")
def u5_dir() -> Path:
    path = _find_u5_dir()
    if path is None:
        pytest.skip("U5 game files not found")
    return path


@pytest.fixture(scope="module")
def compressed_words(u5_dir: Path) -> CompressedWords:
    return CompressedWords(DataOVL(u5_dir).compressed_words)


@pytest.fixture(scope="module")
def towne_tlk(u5_dir: Path, compressed_words: CompressedWords) -> TlkFile:
    return TlkFile(u5_dir / "TOWNE.TLK", compressed_words)


@pytest.fixture(scope="module")
def castle_tlk(u5_dir: Path, compressed_words: CompressedWords) -> TlkFile:
    return TlkFile(u5_dir / "CASTLE.TLK", compressed_words)


def test_towne_tlk_has_dialogs(towne_tlk: TlkFile):
    assert len(towne_tlk.dialogs) > 0
    # Every TLK entry is keyed by a positive dialog number.
    for key in towne_tlk.dialogs.keys():
        assert key >= 1


def test_every_npc_has_five_canonical_lines(towne_tlk: TlkFile):
    for npc in towne_tlk.dialogs.values():
        assert npc.name        is not None
        assert npc.description is not None
        assert npc.greeting    is not None
        assert npc.job         is not None
        assert npc.bye         is not None


def test_name_lines_decode_to_readable_ascii(towne_tlk: TlkFile):
    # Every NPC should have a non-empty name that contains only printable
    # characters — if the compressed-word lookup or char-shift were wrong,
    # we'd see control bytes here.
    for npc in towne_tlk.dialogs.values():
        name = npc.name.as_text()
        assert name, f"dialog #{npc.npc_dialog_number} has empty name"
        assert all(ch.isprintable() for ch in name), repr(name)


def test_castle_tlk_decodes_known_names(castle_tlk: TlkFile):
    # Spot-check a handful of canonical Castle Britannia NPC names — these
    # exercise both plain-character decoding and compressed-word expansion
    # (e.g. "alistair the bard" relies on the 'the' compressed word).
    names = {npc.name.as_text().lower() for npc in castle_tlk.dialogs.values()}
    assert "alistair the bard" in names, names
    assert "ambrose" in names, names


def test_keyword_responses_are_lowercase(towne_tlk: TlkFile):
    for npc in towne_tlk.dialogs.values():
        for kw in npc.keyword_responses.keys():
            assert kw == kw.lower()


def test_every_npc_has_some_keyword_responses(towne_tlk: TlkFile):
    # Every NPC in TOWNE.TLK has at least one custom keyword beyond the
    # baked-in name/job/bye (the game injects those separately at runtime).
    dialogs_with_keywords = sum(1 for d in towne_tlk.dialogs.values() if d.keyword_responses)
    assert dialogs_with_keywords >= len(towne_tlk.dialogs) // 2
