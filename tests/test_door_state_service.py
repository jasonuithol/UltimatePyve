import random

import pytest

from dark_libraries.dark_math import Coord
from models.enums.door_type_tile_id import DoorTypeTileId
from models.enums.inventory_offset  import InventoryOffset
from models.global_location import GlobalLocation
from services.door_state_service import DoorStateService


LOC = 1
LVL = 0
DOOR_COORD = Coord[int](5, 5)
DOOR_LOCATION = GlobalLocation(LOC, LVL, DOOR_COORD)


class _FakeMapLevel:
    def __init__(self, initial_tile_id: int):
        self._tiles: dict[Coord[int], int] = {DOOR_COORD: initial_tile_id}

    def get_tile_id(self, coord: Coord[int]):
        return self._tiles[coord]

    def set_tile_id(self, coord: Coord[int], tile_id: int):
        self._tiles[coord] = tile_id


class _FakeU5Map:
    def __init__(self, map_level: _FakeMapLevel):
        self._map_level = map_level

    def get_tile_id(self, _level_index, coord):
        return self._map_level.get_tile_id(coord)

    def get_map_level(self, _level_index):
        return self._map_level


class _FakeMapsRegistry:
    def __init__(self, u5_map: _FakeU5Map):
        self._u5_map = u5_map

    def get(self, _location_index):
        return self._u5_map


class _FakeSavedGame:
    def __init__(self, keys: int):
        self._mem = {InventoryOffset.KEYS: keys}

    def read_u8(self, offset):
        return self._mem.get(offset, 0)

    def write_u8(self, offset, value):
        self._mem[offset] = value


class _FakeGlobalRegistry:
    def __init__(self, u5_map: _FakeU5Map, saved_game: _FakeSavedGame):
        self.maps = _FakeMapsRegistry(u5_map)
        self.saved_game = saved_game


class _FakeConsoleService:
    def __init__(self):
        self.messages: list[str] = []

    def print_ascii(self, text, include_carriage_return=True):
        self.messages.append(text)


class _FakeMapCacheService:
    def __init__(self):
        self.refresh_calls: list[tuple[int, int, Coord[int]]] = []

    def refresh_coord(self, location_index, level_index, coord):
        self.refresh_calls.append((location_index, level_index, coord))


def _build(initial_tile_id: int, keys: int = 0) -> DoorStateService:
    map_level = _FakeMapLevel(initial_tile_id)
    u5_map = _FakeU5Map(map_level)
    saved_game = _FakeSavedGame(keys)

    service = DoorStateService()
    service.global_registry   = _FakeGlobalRegistry(u5_map, saved_game)
    service.console_service   = _FakeConsoleService()
    service.map_cache_service = _FakeMapCacheService()
    # Expose for assertions.
    service._map_level = map_level
    service._saved_game = saved_game
    return service


def _tile(service: DoorStateService) -> int:
    return service._map_level.get_tile_id(DOOR_COORD)


# is_door_tile --------------------------------------------------------------

@pytest.mark.parametrize("tile_id", [
    DoorTypeTileId.D_UNLOCKED_NORMAL.value,
    DoorTypeTileId.D_UNLOCKED_WINDOWED.value,
    DoorTypeTileId.D_LOCKED_NORMAL.value,
    DoorTypeTileId.D_LOCKED_WINDOWED.value,
    DoorTypeTileId.D_MAGIC_NORMAL.value,
    DoorTypeTileId.D_MAGIC_WINDOWED.value,
])
def test_is_door_tile_accepts_closed_variants(tile_id):
    assert DoorStateService.is_door_tile(tile_id)


def test_is_door_tile_rejects_opened_tile():
    # D_OPENED is the tiled-floor tile — not a door from the spawner's POV.
    assert not DoorStateService.is_door_tile(DoorTypeTileId.D_OPENED.value)


def test_is_door_tile_rejects_arbitrary_tile():
    assert not DoorStateService.is_door_tile(5)


# try_move_into -------------------------------------------------------------

def test_try_move_into_opens_an_unlocked_door():
    service = _build(DoorTypeTileId.D_UNLOCKED_NORMAL.value)

    result = service.try_move_into(DOOR_LOCATION)

    assert result.traversal_allowed is False
    assert result.alternative_action_taken is True
    assert _tile(service) == DoorTypeTileId.D_OPENED.value
    assert service.map_cache_service.refresh_calls == [(LOC, LVL, DOOR_COORD)]


def test_try_move_into_an_opened_door_allows_traversal():
    service = _build(DoorTypeTileId.D_UNLOCKED_NORMAL.value)
    service.try_move_into(DOOR_LOCATION)  # open it first

    result = service.try_move_into(DOOR_LOCATION)

    assert result.traversal_allowed is True
    assert result.alternative_action_taken is False


def test_try_move_into_a_key_locked_door_is_a_bump():
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value)

    result = service.try_move_into(DOOR_LOCATION)

    assert result.traversal_allowed is False
    assert result.alternative_action_taken is False
    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value


def test_try_move_into_a_magic_locked_door_is_a_bump():
    service = _build(DoorTypeTileId.D_MAGIC_NORMAL.value)

    result = service.try_move_into(DOOR_LOCATION)

    assert result.traversal_allowed is False
    assert result.alternative_action_taken is False
    assert _tile(service) == DoorTypeTileId.D_MAGIC_NORMAL.value


# pass_time / auto-close ----------------------------------------------------

def test_opened_door_closes_to_unlocked_after_four_turns():
    service = _build(DoorTypeTileId.D_UNLOCKED_NORMAL.value)
    service.try_move_into(DOOR_LOCATION)

    for _ in range(3):
        service.pass_time(DOOR_LOCATION)
        assert _tile(service) == DoorTypeTileId.D_OPENED.value

    service.pass_time(DOOR_LOCATION)
    assert _tile(service) == DoorTypeTileId.D_UNLOCKED_NORMAL.value


def test_windowed_door_closes_back_to_windowed_unlocked():
    service = _build(DoorTypeTileId.D_UNLOCKED_WINDOWED.value)
    service.try_move_into(DOOR_LOCATION)

    for _ in range(4):
        service.pass_time(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_UNLOCKED_WINDOWED.value


# try_jimmy -----------------------------------------------------------------

def test_jimmy_without_keys_prints_and_changes_nothing():
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value, keys=0)

    service.try_jimmy(DOOR_LOCATION)

    assert "No Keys !" in service.console_service.messages
    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value


def test_jimmy_success_unlocks_and_keeps_key(monkeypatch):
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value, keys=3)
    monkeypatch.setattr(random, "choice", lambda seq: True)

    service.try_jimmy(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_UNLOCKED_NORMAL.value
    assert service._saved_game.read_u8(InventoryOffset.KEYS) == 3
    assert "Unlocked !" in service.console_service.messages


def test_jimmy_failure_breaks_a_key(monkeypatch):
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value, keys=3)
    monkeypatch.setattr(random, "choice", lambda seq: False)

    service.try_jimmy(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value
    assert service._saved_game.read_u8(InventoryOffset.KEYS) == 2
    assert "Key broke !" in service.console_service.messages


def test_jimmy_against_magic_door_always_breaks_a_key(monkeypatch):
    service = _build(DoorTypeTileId.D_MAGIC_NORMAL.value, keys=2)
    # force_success would still be irrelevant — magic doors never jimmy open.
    monkeypatch.setattr(random, "choice", lambda seq: True)

    service.try_jimmy(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_MAGIC_NORMAL.value
    assert service._saved_game.read_u8(InventoryOffset.KEYS) == 1
    assert "Key broke !" in service.console_service.messages


def test_jimmy_on_unlocked_door_is_a_no_op():
    service = _build(DoorTypeTileId.D_UNLOCKED_NORMAL.value, keys=3)

    service.try_jimmy(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_UNLOCKED_NORMAL.value
    assert service._saved_game.read_u8(InventoryOffset.KEYS) == 3


# try_magic_unlock ----------------------------------------------------------

def test_magic_unlock_opens_a_magic_door():
    service = _build(DoorTypeTileId.D_MAGIC_NORMAL.value)

    service.try_magic_unlock(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_UNLOCKED_NORMAL.value


def test_magic_unlock_ignores_a_key_locked_door():
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value)

    service.try_magic_unlock(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value


# level_changed -------------------------------------------------------------

def test_level_changed_restores_mutated_tiles_and_clears_timers(monkeypatch):
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value, keys=3)
    monkeypatch.setattr(random, "choice", lambda seq: True)

    service.try_jimmy(DOOR_LOCATION)       # D_LOCKED_NORMAL -> D_UNLOCKED_NORMAL
    service.try_move_into(DOOR_LOCATION)   # -> D_OPENED, timer armed
    assert _tile(service) == DoorTypeTileId.D_OPENED.value

    service.level_changed(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value
    assert service._opening_timers == {}
    assert service._original_tiles == {}


def test_level_changed_with_no_mutations_is_a_no_op():
    service = _build(DoorTypeTileId.D_LOCKED_NORMAL.value)

    service.level_changed(DOOR_LOCATION)

    assert _tile(service) == DoorTypeTileId.D_LOCKED_NORMAL.value
    assert service.map_cache_service.refresh_calls == []
