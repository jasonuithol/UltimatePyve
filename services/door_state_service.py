import random

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging     import LoggerMixin

from data.global_registry import GlobalRegistry
from models.enums.door_type_tile_id import DoorTypeTileId
from models.enums.inventory_offset  import InventoryOffset
from models.global_location         import GlobalLocation
from models.move_into_result        import MoveIntoResult
from services.console_service       import ConsoleService
from services.map_cache.map_cache_service import MapCacheService


_TURNS_UNTIL_CLOSE = 4

_DOOR_TILE_IDS: set[int] = {
    door.value for door in DoorTypeTileId if door != DoorTypeTileId.D_OPENED
}
_UNLOCKED_TILE_IDS: set[int] = {
    DoorTypeTileId.D_UNLOCKED_NORMAL.value,
    DoorTypeTileId.D_UNLOCKED_WINDOWED.value,
}
_KEY_LOCKED_TILE_IDS: set[int] = {
    DoorTypeTileId.D_LOCKED_NORMAL.value,
    DoorTypeTileId.D_LOCKED_WINDOWED.value,
}
_MAGIC_LOCKED_TILE_IDS: set[int] = {
    DoorTypeTileId.D_MAGIC_NORMAL.value,
    DoorTypeTileId.D_MAGIC_WINDOWED.value,
}
_WINDOWED_TILE_IDS: set[int] = {
    DoorTypeTileId.D_UNLOCKED_WINDOWED.value,
    DoorTypeTileId.D_LOCKED_WINDOWED.value,
    DoorTypeTileId.D_MAGIC_WINDOWED.value,
}


class DoorStateService(LoggerMixin, DarkEventListenerMixin):

    # Injectable
    global_registry:   GlobalRegistry
    console_service:   ConsoleService
    map_cache_service: MapCacheService

    def __init__(self):
        super().__init__()
        # GlobalLocation -> turns_until_close
        self._opening_timers: dict[GlobalLocation, int] = {}
        # GlobalLocation -> original tile_id (before any mutation)
        self._original_tiles: dict[GlobalLocation, int] = {}

    @classmethod
    def is_door_tile(cls, tile_id: int) -> bool:
        return tile_id in _DOOR_TILE_IDS

    # DarkEventListenerMixin: start
    def level_changed(self, party_location: GlobalLocation):
        # Restore every tile we mutated on the old level — doors revert to their
        # original locked/closed state when the party leaves, matching the OG.
        for door_location, original_tile_id in self._original_tiles.items():
            self._write_tile(door_location, original_tile_id)
        self._original_tiles.clear()
        self._opening_timers.clear()

    def pass_time(self, party_location: GlobalLocation):
        # Count down every open door; close when the counter hits zero.
        expired: list[GlobalLocation] = []
        for door_location in list(self._opening_timers.keys()):
            self._opening_timers[door_location] -= 1
            if self._opening_timers[door_location] <= 0:
                self._close(door_location)
                expired.append(door_location)
        for door_location in expired:
            del self._opening_timers[door_location]
    # DarkEventListenerMixin: end

    def try_move_into(self, door_location: GlobalLocation) -> MoveIntoResult:
        tile_id = self._read_tile(door_location)
        if tile_id == DoorTypeTileId.D_OPENED.value:
            return MoveIntoResult(traversal_allowed=True, alternative_action_taken=False)
        if tile_id in _UNLOCKED_TILE_IDS:
            self._open(door_location)
            return MoveIntoResult(traversal_allowed=False, alternative_action_taken=True)
        # locked (key or magic) — bump only.
        return MoveIntoResult(traversal_allowed=False, alternative_action_taken=False)

    def try_jimmy(self, door_location: GlobalLocation):
        self._jimmy(door_location, force_success=False)

    def try_magic_unlock(self, door_location: GlobalLocation):
        tile_id = self._read_tile(door_location)
        if tile_id not in _MAGIC_LOCKED_TILE_IDS:
            return
        self._become_unlocked(door_location)

    # Internal helpers

    def _open(self, door_location: GlobalLocation):
        self._write_tile(door_location, DoorTypeTileId.D_OPENED.value)
        self._opening_timers[door_location] = _TURNS_UNTIL_CLOSE

    def _close(self, door_location: GlobalLocation):
        self._become_unlocked(door_location)

    def _become_unlocked(self, door_location: GlobalLocation):
        original_tile_id = self._original_tiles.get(door_location, self._read_tile(door_location))
        if original_tile_id in _WINDOWED_TILE_IDS:
            self._write_tile(door_location, DoorTypeTileId.D_UNLOCKED_WINDOWED.value)
        else:
            self._write_tile(door_location, DoorTypeTileId.D_UNLOCKED_NORMAL.value)

    def _jimmy(self, door_location: GlobalLocation, force_success: bool):
        saved_game = self.global_registry.saved_game
        if saved_game.read_u8(InventoryOffset.KEYS) == 0:
            self.console_service.print_ascii("No Keys !")
            return
        tile_id = self._read_tile(door_location)
        if tile_id == DoorTypeTileId.D_OPENED.value:
            return
        if tile_id in _UNLOCKED_TILE_IDS:
            return
        if tile_id in _MAGIC_LOCKED_TILE_IDS:
            self._break_key()
            return
        if tile_id not in _KEY_LOCKED_TILE_IDS:
            return
        success = force_success or random.choice([True, False])
        if success:
            self._become_unlocked(door_location)
            self.console_service.print_ascii("Unlocked !")
            return
        self._break_key()

    def _break_key(self):
        saved_game = self.global_registry.saved_game
        current_keys = saved_game.read_u8(InventoryOffset.KEYS)
        saved_game.write_u8(InventoryOffset.KEYS, current_keys - 1)
        self.console_service.print_ascii("Key broke !")

    def _read_tile(self, door_location: GlobalLocation) -> int:
        u5_map = self.global_registry.maps.get(door_location.location_index)
        return u5_map.get_tile_id(door_location.level_index, door_location.coord)

    def _write_tile(self, door_location: GlobalLocation, tile_id: int):
        u5_map = self.global_registry.maps.get(door_location.location_index)
        map_level = u5_map.get_map_level(door_location.level_index)
        # Remember the pre-mutation tile so level_changed can restore it.
        if door_location not in self._original_tiles:
            self._original_tiles[door_location] = map_level.get_tile_id(door_location.coord)
        map_level.set_tile_id(door_location.coord, tile_id)
        self.map_cache_service.refresh_coord(
            door_location.location_index,
            door_location.level_index,
            door_location.coord,
        )
