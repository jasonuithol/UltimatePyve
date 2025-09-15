import random

from dark_libraries import immutable, Coord

from game.magic import S_MAGIC_UNLOCK
from items.consumable_items import ConsumableItemType

from .interactable import Interactable
from .interactable_factory import InteractableFactory
from .interaction_result import InteractionResult

@immutable
class DoorType(InteractableFactory):

    # Tile types.
    D_OPENED              = 68

    D_UNLOCKED_NORMAL     = 184
    D_UNLOCKED_WINDOWED   = 186

    D_LOCKED_NORMAL       = 185
    D_LOCKED_WINDOWED     = 187

    D_MAGIC_NORMAL        = 151
    D_MAGIC_WINDOWED      = 152

    # Original lock states
    L_UNLOCKED = 0
    L_KEY_LOCKED = 1
    L_MAGIC_LOCKED = 2

    def __init__(self, tile_id: bool):
        # Set Permanent state
        self.original_tile_id: int  = tile_id

        self.original_windowed: bool = (
            tile_id in [
                DoorType.D_UNLOCKED_WINDOWED, 
                DoorType.D_LOCKED_WINDOWED, 
                DoorType.D_MAGIC_WINDOWED
            ]
        )

        if tile_id in [DoorType.D_UNLOCKED_NORMAL, DoorType.D_UNLOCKED_WINDOWED]:
            self.original_lock_type = DoorType.L_UNLOCKED
            return
        if tile_id in [DoorType.D_LOCKED_NORMAL, DoorType.D_LOCKED_WINDOWED]:
            self.original_lock_type = DoorType.L_KEY_LOCKED
            return
        if tile_id in [DoorType.D_MAGIC_NORMAL, DoorType.D_MAGIC_WINDOWED]:
            self.original_lock_type = DoorType.L_MAGIC_LOCKED
            return

        raise ValueError(f"Unknown original tile_id for doors: {tile_id}")

    def create_interactable(self, coord: Coord) -> 'DoorInstance':
        return DoorInstance(door_type=self, coord=coord)

    @classmethod
    def is_door_tile(cls, tile_id: int):
        return tile_id in [
            cls.D_UNLOCKED_NORMAL,
            cls.D_UNLOCKED_WINDOWED,
            cls.D_LOCKED_NORMAL,
            cls.D_LOCKED_WINDOWED,
            cls.D_MAGIC_NORMAL,
            cls.D_MAGIC_WINDOWED,
        ]

class DoorInstance(Interactable):
    def __init__(self, door_type: DoorType, coord: Coord):
        self.door_type: DoorType = door_type
        self.coord = coord

        # Set Current state
        self._restore()

    def _restore(self) -> None:
        self.tile_id:   int     = self.door_type.original_tile_id
        self.is_locked: bool    = self.door_type.original_lock_type in [DoorType.L_KEY_LOCKED, DoorType.L_MAGIC_LOCKED]
        self.is_open:   bool    = False
        self.turns_until_close: int = 0

    def _close(self) -> None:
        self._become_unlocked()

    def _become_unlocked(self) -> None:
        self.is_open = False
        self.is_locked = False

        print(f"Becoming unlocked: original_tile_id={self.door_type.original_tile_id} windowed={self.door_type.original_windowed}")

        if self.door_type.original_windowed == True:
            self.tile_id = DoorType.D_UNLOCKED_WINDOWED
        else:
            self.tile_id = DoorType.D_UNLOCKED_NORMAL

    def _jimmy(self, force_success: bool = False) -> str:
        if self.is_open:
            return InteractionResult.R_NOTHING_THERE
        if not self.is_locked:
            return InteractionResult.R_NOTHING_THERE
        if self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            return InteractionResult.R_KEYBROKE

        success = force_success or random.choice([True, False])
        if success:
            self._become_unlocked()
            return InteractionResult.R_LOUD_SUCCESS
        else:
            return InteractionResult.R_KEYBROKE
        
    def _open(self) -> str:
        if self.is_open:
            return InteractionResult.R_NOTHING_THERE
        if self.is_locked:
            return InteractionResult.R_LOCKED

        self.is_open = True
        self.tile_id = DoorType.D_OPENED
        self.turns_until_close = 4

        return InteractionResult.R_QUIET_SUCCESS

    def _magic_unlock(self) -> str:
        if self.is_open:
            return InteractionResult.R_NOTHING_THERE
        if not self.is_locked:
            return InteractionResult.R_NOTHING_THERE
        if not self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            return InteractionResult.R_NOTHING_THERE
        
        self._become_unlocked()

        return InteractionResult.R_LOUD_SUCCESS

    # Interactable implementation: Start
    def get_current_tile_id(self):
        return self.tile_id

    '''
    def create_sprite(self) -> Sprite:
        frame = self.door_type.tileset.tiles[self.tile_id]
        sprite = Sprite(
            frames=[frame]
        )
        return sprite
    '''

    def pass_time(self):
        if self.is_open and self.turns_until_close > 0:
            self.turns_until_close -= 1

            print(f"DOOR OPEN: Turns until door closes {self.turns_until_close}")

            if self.turns_until_close == 0:
                self._close()

    def move_into(self, actor=None) -> InteractionResult:
        if self.is_open:
            msg = InteractionResult.R_QUIET_SUCCESS
        else:
            msg = self._open()
        return InteractionResult.result(msg)

    def jimmy(self, actor=None) -> InteractionResult:
        msg = self._jimmy()
        return InteractionResult.result(msg)
    
    def use_item_on(self, item, actor=None) -> InteractionResult:
        raise NotImplementedError()
        if item != ConsumableItemType.I_SKULL_KEY:
            return InteractionResult.error()
        return InteractionResult.result(self._magic_unlock())

    def cast_spell_on(self, spell, actor=None):
        raise NotImplementedError()
        if spell != S_MAGIC_UNLOCK:
            return InteractionResult.error()
        return InteractionResult.result(self._magic_unlock())
    # Interactable implementation: End