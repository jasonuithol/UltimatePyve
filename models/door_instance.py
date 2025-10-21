import random

from dark_libraries.dark_math        import Coord
from dark_libraries.service_provider import ServiceProvider

from data.global_registry import GlobalRegistry
from models.door_type        import DoorType
from models.enums.door_type_tile_id import DoorTypeTileId
from models.global_location import GlobalLocation
from models.magic            import S_MAGIC_UNLOCK
from models.enums.inventory_offset  import InventoryOffset
from models.move_into_result import MoveIntoResult
from models.interactable     import Interactable

from services.console_service import ConsoleService

class DoorInstance(Interactable):
    def __init__(self, door_type: DoorType, coord: Coord):
        assert not door_type is None, "door_type cannot be None"
        self.door_type: DoorType = door_type
        self.coord: Coord = coord
        self.console_service: ConsoleService = ServiceProvider.get_provider().resolve(ConsoleService)
        self.global_registry: GlobalRegistry = ServiceProvider.get_provider().resolve(GlobalRegistry)

        # Set Current state
        self._restore()

    def _restore(self) -> None:
        self.tile_id:   int  = self.door_type.original_tile_id
        self.is_locked: bool = self.door_type.original_lock_type in [DoorType.L_KEY_LOCKED, DoorType.L_MAGIC_LOCKED]
        self.is_open:   bool = False
        self.turns_until_close: int = 0

    def _close(self) -> None:
        self._become_unlocked()

    def _become_unlocked(self) -> None:
        self.is_open = False
        self.is_locked = False

        print(f"Becoming unlocked: original_tile_id={self.door_type.original_tile_id} windowed={self.door_type.original_windowed}")

        if self.door_type.original_windowed == True:
            self.tile_id = DoorTypeTileId.D_UNLOCKED_WINDOWED.value
        else:
            self.tile_id = DoorTypeTileId.D_UNLOCKED_NORMAL.value

    def _break_key(self):
        current_keys = self.global_registry.saved_game.read_u8(InventoryOffset.KEYS)
        self.global_registry.saved_game.write_u8(InventoryOffset.KEYS, current_keys - 1)
        self.console_service.print_ascii("Key broke !")

    def _jimmy(self, force_success: bool = False):
        if self.global_registry.saved_game.read_u8(InventoryOffset.KEYS) == 0:
            self.console_service.print_ascii("No Keys !")
            return
        if self.is_open:
            return
        if not self.is_locked:
            return
        if self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            self._break_key()
            return

        success = force_success or random.choice([True, False])
        if success:
            self._become_unlocked()
            self.console_service.print_ascii("Unlocked !")
            return

        self._break_key()
    
    def _magic_unlock(self):
        if self.is_open:
            return
        if not self.is_locked:
            return
        if not self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            return
        self._become_unlocked()

    # Interactable implementation: Start
    def get_current_tile_id(self):
        return self.tile_id

    def pass_time(self, party_location: GlobalLocation):
        if self.is_open and self.turns_until_close > 0:
            self.turns_until_close -= 1

            print(f"DOOR OPEN: Turns until door closes {self.turns_until_close}")

            if self.turns_until_close == 0:
                self._close()

    def move_into(self) -> MoveIntoResult:
        if self.is_open:
            return MoveIntoResult(traversal_allowed = True, alternative_action_taken = False)
        else:
            self.open()
            if self.is_open:
                return MoveIntoResult(traversal_allowed = False, alternative_action_taken = True)
            else:
                return MoveIntoResult(traversal_allowed = False, alternative_action_taken = False)

    def open(self):
        if self.is_open:
            return
        if self.is_locked:
            return

        self.is_open = True
        self.tile_id = DoorTypeTileId.D_OPENED.value
        self.turns_until_close = 4
    
    def jimmy(self):
        return self._jimmy(force_success=False)
    # Interactable implementation: End