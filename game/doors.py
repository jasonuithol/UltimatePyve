# file: doors.py
from typing import Dict
import random

from dark_libraries.dark_math import Coord
from dark_libraries.custom_decorators import immutable
from loaders.tileset import load_tiles16_raw, TILES16_PATH

from game.magic import S_MAGIC_UNLOCK
from animation.sprite import Sprite
from game.usable_items import UsableItem
from game.interactable import Interactable, InteractableFactory, InteractionResult, R_KEYBROKE, R_LOCKED, R_LOUD_SUCCESS, R_NOTHING_THERE, R_QUIET_SUCCESS

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

@immutable
class DoorType(InteractableFactory):
    def __init__(self, tile_id: bool, lock_type: int, windowed: bool):
        # Set Permanent state
        self.original_tile_id:      int  = tile_id
        self.original_lock_type:    int = lock_type
        self.original_windowed:     bool = windowed

    def create_interactable(self, coord: Coord) -> 'DoorInstance':
        return DoorInstance(door_type=self, coord=coord)

    @classmethod
    def is_door_tile(cls, tile_id: int):
        return tile_id in [
            D_UNLOCKED_NORMAL,
            D_UNLOCKED_WINDOWED,
            D_LOCKED_NORMAL,
            D_LOCKED_WINDOWED,
            D_MAGIC_NORMAL,
            D_MAGIC_WINDOWED,
        ]

class DoorInstance(Interactable):
    def __init__(self, door_type: DoorType, coord: Coord):
        self.door_type: DoorType = door_type
        self.coord = coord

        # Set Current state
        self._restore()

    def _restore(self) -> None:
        self.tile_id:   int     = self.door_type.original_tile_id
        self.is_locked: bool    = self.door_type.original_lock_type in [L_KEY_LOCKED, L_MAGIC_LOCKED]
        self.is_open:   bool    = False

    def _close(self) -> None:
        self._become_unlocked()

    def _become_unlocked(self) -> None:
        self.is_open = False
        self.is_locked = False

        if self.door_type.original_windowed:
            self.tile_id = D_UNLOCKED_WINDOWED
        else:
            self.tile_id = D_UNLOCKED_NORMAL

    def _jimmy(self, force_success: bool = False) -> str:
        if self.is_open:
            return R_NOTHING_THERE
        if not self.is_locked:
            return R_NOTHING_THERE
        if self.door_type.original_lock_type == L_MAGIC_LOCKED:
            return R_KEYBROKE

        success = force_success or random.choice(True, False)
        if success:
            self._become_unlocked()
            return R_LOUD_SUCCESS
        else:
            return R_KEYBROKE
        
    def _open(self) -> str:
        if self.is_open:
            return R_NOTHING_THERE
        if self.is_locked:
            return R_LOCKED

        self.is_open = True
        self.tile_id = D_OPENED

        return R_QUIET_SUCCESS

    def _magic_unlock(self) -> str:
        if self.is_open:
            return R_NOTHING_THERE
        if not self.is_locked:
            return R_NOTHING_THERE
        if not self.door_type.original_lock_type == L_MAGIC_LOCKED:
            return R_NOTHING_THERE
        
        self._become_unlocked()

        return R_LOUD_SUCCESS

    # Interactable implementation: Start
    def create_sprite(self) -> Sprite:
        frame = load_tiles16_raw(TILES16_PATH)[self.tile_id]
        sprite = Sprite(
            frames=[frame]
        )
        sprite.world_coord = self.coord
        return sprite

    def move_into(self, actor=None) -> InteractionResult:
        if self.is_open:
            msg = R_QUIET_SUCCESS
        else:
            msg = self._open()
        return InteractionResult.result(msg)

    def jimmy(self, actor=None) -> InteractionResult:
        msg = self._jimmy()
        return InteractionResult.result(msg)
    
    def use_item_on(self, item, actor=None) -> InteractionResult:
        if item != UsableItem.I_SKULL_KEY:
            return InteractionResult.error()
        return InteractionResult.result(self._magic_unlock())

    def cast_spell_on(self, spell, actor=None):
        if spell != S_MAGIC_UNLOCK:
            return InteractionResult.error()
        return InteractionResult.result(self._magic_unlock())
    # Interactable implementation: End


#
# Globals
#
_door_types: Dict[int, DoorType] = None

def build_all_door_types() -> Dict[int, DoorType]:
    global _door_types
    if _door_types is None:
        _door_types = {}
        for door in [
            #                               lock_type       windowed
            #                               --------------  --------
            DoorType(D_MAGIC_NORMAL,        L_MAGIC_LOCKED, False),
            DoorType(D_MAGIC_WINDOWED,      L_MAGIC_LOCKED, True ),

            DoorType(D_UNLOCKED_NORMAL,     L_UNLOCKED,     False),
            DoorType(D_UNLOCKED_WINDOWED,   L_UNLOCKED,     True ),

            DoorType(D_LOCKED_NORMAL,       L_KEY_LOCKED,   False),
            DoorType(D_LOCKED_WINDOWED,     L_KEY_LOCKED,   True ),
        ]:
            _door_types[door.original_tile_id] = door

        return _door_types

#
# main
#
if __name__ == "__main__":

    doors = build_all_door_types()

    # unlock tests
    assert doors[D_LOCKED_NORMAL].create_instance().jimmy(force_success=True).tile_id == D_UNLOCKED_NORMAL, "door 185 failed jimmy test"
    assert doors[D_LOCKED_WINDOWED].create_instance().jimmy(force_success=True).tile_id == D_UNLOCKED_WINDOWED, "door 187 failed jimmy test"

    assert doors[D_MAGIC_NORMAL].create_instance().magic_unlock().tile_id == D_UNLOCKED_NORMAL, "door 185 failed magic test"
    assert doors[D_MAGIC_WINDOWED].create_instance().magic_unlock().tile_id == D_UNLOCKED_WINDOWED, "door 187 failed magic test"

    # Open tests
    assert doors[D_UNLOCKED_NORMAL].create_instance().open().tile_id == D_OPENED, "door 184 failed open test"
    assert doors[D_UNLOCKED_WINDOWED].create_instance().open().tile_id == D_OPENED, "door 186 failed open test"

    assert doors[D_LOCKED_NORMAL].create_instance().jimmy(force_success=True).open().tile_id == D_OPENED, "door 185 failed open test"
    assert doors[D_LOCKED_WINDOWED].create_instance().jimmy(force_success=True).open().tile_id == D_OPENED, "door 187 failed open test"

    assert doors[D_MAGIC_NORMAL].create_instance().magic_unlock().open().tile_id == D_OPENED, "door 151 failed open test"
    assert doors[D_LOCKED_NORMAL].create_instance().magic_unlock().open().tile_id == D_OPENED, "door 152 failed open test"

    print("All tests passed.")

