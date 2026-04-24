from pathlib import Path

import pytest

from data.global_registry    import GlobalRegistry
from data.loaders.npc_file_loader import NpcFileLoader
from models.location_metadata import LocationMetadata
from models.npc_file import NpcMapSection


NPC_FILE_NAMES = ("TOWNE.NPC", "DWELLING.NPC", "CASTLE.NPC", "KEEP.NPC")


def _find_u5_dir() -> Path | None:
    try:
        from configure import get_u5_path
        return get_u5_path()
    except AssertionError:
        pass
    repo_local = Path(__file__).resolve().parents[1] / "u5"
    if all((repo_local / name).exists() for name in NPC_FILE_NAMES):
        return repo_local
    return None


@pytest.fixture(scope="module")
def u5_dir() -> Path:
    path = _find_u5_dir()
    if path is None:
        pytest.skip("U5 game files not found")
    return path


def _meta(location_index: int, files_index: int | None, group_index: int | None) -> LocationMetadata:
    return LocationMetadata(
        location_index   = location_index,
        name             = f"LOC{location_index}",
        name_index       = 0,
        files_index      = files_index,
        group_index      = group_index,
        map_index_offset = 0,
        num_levels       = 1,
        default_level    = 0,
        has_basement     = False,
        trigger_index    = location_index - 1,
        sound_track      = None,
    )


def _run_loader(u5_dir: Path, metadata: list[LocationMetadata]) -> GlobalRegistry:
    registry = GlobalRegistry()
    loader = NpcFileLoader()
    loader.global_registry = registry
    loader.load(u5_dir, metadata)
    return registry


def test_loader_registers_one_section_per_registered_town(u5_dir: Path):
    samples = [
        (1,  0, 0),   # TOWNE: Moonglow
        (2,  0, 1),   # TOWNE: Britain
        (9,  1, 0),   # DWELLING: Fogsbane
        (17, 2, 0),   # CASTLE: Lord British's
        (25, 3, 0),   # KEEP: Ararat
    ]
    metadata = [_meta(loc, fidx, gidx) for loc, fidx, gidx in samples]
    registry = _run_loader(u5_dir, metadata)

    assert len(registry.npc_sections) == len(samples)
    for loc, _, _ in samples:
        section = registry.npc_sections.get(loc)
        assert isinstance(section, NpcMapSection)
        assert len(section.schedules) == 32
        assert len(section.types) == 32
        assert len(section.dialog_numbers) == 32


def test_loader_skips_overworld_entries(u5_dir: Path):
    metadata = [
        _meta(0, None, None),   # overworld sentinel
        _meta(1, 0, 0),
    ]
    registry = _run_loader(u5_dir, metadata)

    assert registry.npc_sections.get(0) is None
    assert registry.npc_sections.get(1) is not None


def test_loader_ties_each_file_to_its_full_cohort(u5_dir: Path):
    # All 8 sections of KEEP.NPC (files_index=3).
    metadata = [_meta(100 + gi, 3, gi) for gi in range(8)]
    registry = _run_loader(u5_dir, metadata)

    for group_index in range(8):
        section = registry.npc_sections.get(100 + group_index)
        assert section is not None
        assert any(not s.is_empty() for s in section.schedules), f"group {group_index} is entirely empty"
