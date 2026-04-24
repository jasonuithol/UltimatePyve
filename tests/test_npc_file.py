from pathlib import Path

import pytest

from models.npc_file import NpcFile, NpcSchedule


NPC_FILE_NAMES = ("TOWNE.NPC", "DWELLING.NPC", "CASTLE.NPC", "KEEP.NPC")


def _find_u5_dir() -> Path | None:
    # Prefer the project's configured lookup (dev install / GOG / Mac app).
    try:
        from configure import get_u5_path
        return get_u5_path()
    except AssertionError:
        pass
    # Fallback: repo-local u5/ (gitignored; present in this dev container).
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


@pytest.fixture(scope="module", params=NPC_FILE_NAMES)
def npc_file(request, u5_dir: Path) -> NpcFile:
    return NpcFile(u5_dir / request.param)


def test_file_parses_to_eight_map_sections(npc_file: NpcFile):
    assert len(npc_file.maps) == 8


def test_slot_zero_schedule_is_zero_filled(npc_file: NpcFile):
    for map_index, section in enumerate(npc_file.maps):
        assert section.schedules[0].is_empty(), f"map {map_index} slot 0 not empty"


def test_slot_zero_dialog_number_is_zero(npc_file: NpcFile):
    for map_index, section in enumerate(npc_file.maps):
        assert section.dialog_numbers[0] == 0, f"map {map_index} slot 0 dialog non-zero"


def test_active_schedules_have_valid_xy(npc_file: NpcFile):
    for map_index, section in enumerate(npc_file.maps):
        for slot, schedule in enumerate(section.schedules):
            if schedule.is_empty():
                continue
            for c in schedule.x_coords:
                assert 0 <= c <= 31, f"map {map_index} slot {slot} bad X {c}"
            for c in schedule.y_coords:
                assert 0 <= c <= 31, f"map {map_index} slot {slot} bad Y {c}"


def test_active_schedules_have_valid_z(npc_file: NpcFile):
    # Castles & keeps go up several floors; underworld dwellings use -1.
    # Tight-ish bound — if a real file violates this we learn something.
    for map_index, section in enumerate(npc_file.maps):
        for slot, schedule in enumerate(section.schedules):
            if schedule.is_empty():
                continue
            for c in schedule.z_coords:
                assert -1 <= c <= 5, f"map {map_index} slot {slot} bad Z {c}"


def test_active_schedules_have_valid_times(npc_file: NpcFile):
    for map_index, section in enumerate(npc_file.maps):
        for slot, schedule in enumerate(section.schedules):
            if schedule.is_empty():
                continue
            for t in schedule.times:
                assert 0 <= t <= 23, f"map {map_index} slot {slot} bad time {t}"


def test_schedule_from_bytes_round_trip():
    raw = bytes([
        0, 0, 1,          # AI
        19, 23, 29,       # X
        21, 19, 29,       # Y
        1, 0, 0xFF,       # Z (last one signed → -1)
        21, 9, 17, 18,    # times
    ])
    schedule = NpcSchedule.from_bytes(raw)
    assert schedule.ai_types == (0, 0, 1)
    assert schedule.x_coords == (19, 23, 29)
    assert schedule.y_coords == (21, 19, 29)
    assert schedule.z_coords == (1, 0, -1)
    assert schedule.times    == (21, 9, 17, 18)
    assert not schedule.is_empty()


def test_empty_schedule_detection():
    assert NpcSchedule.from_bytes(bytes(16)).is_empty()


def _schedule_with_times(times: tuple[int, int, int, int]) -> NpcSchedule:
    return NpcSchedule(
        ai_types=(0, 0, 0),
        x_coords=(0, 0, 0),
        y_coords=(0, 0, 0),
        z_coords=(0, 0, 0),
        times=times,
    )


def test_slot_for_hour_all_zero_times_returns_slot_zero():
    schedule = _schedule_with_times((0, 0, 0, 0))
    for hour in range(24):
        assert schedule.slot_for_hour(hour) == 0


def test_slot_for_hour_exact_match_uses_wrap_for_index_three():
    schedule = _schedule_with_times((8, 12, 18, 22))
    assert schedule.slot_for_hour(8)  == 0
    assert schedule.slot_for_hour(12) == 1
    assert schedule.slot_for_hour(18) == 2
    assert schedule.slot_for_hour(22) == 1  # index 3 wraps to slot 1


def test_slot_for_hour_ascending_ranges():
    schedule = _schedule_with_times((8, 12, 18, 22))
    assert schedule.slot_for_hour(10) == 0
    assert schedule.slot_for_hour(15) == 1
    assert schedule.slot_for_hour(20) == 2


def test_slot_for_hour_wraps_around_midnight():
    schedule = _schedule_with_times((8, 12, 18, 22))
    # After the latest time and before the earliest, we're in slot 1.
    assert schedule.slot_for_hour(23) == 1
    assert schedule.slot_for_hour(0)  == 1
    assert schedule.slot_for_hour(2)  == 1
    assert schedule.slot_for_hour(7)  == 1


def test_slot_for_hour_handles_unsorted_times_via_fallback():
    # Times not in ascending order — fallback path must still terminate.
    schedule = _schedule_with_times((22, 8, 12, 18))
    for hour in range(24):
        slot = schedule.slot_for_hour(hour)
        assert slot in (0, 1, 2)


def test_slot_for_hour_real_files_terminate(npc_file):
    # No active schedule should ever fall through to the AssertionError.
    for section in npc_file.maps:
        for schedule in section.schedules:
            if schedule.is_empty():
                continue
            for hour in range(24):
                slot = schedule.slot_for_hour(hour)
                assert slot in (0, 1, 2)
