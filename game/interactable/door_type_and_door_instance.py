import random

from dark_libraries import immutable, Coord

from game.interactable.interactable_factory_registry import InteractableFactoryRegistry
from game.magic import S_MAGIC_UNLOCK
from items.consumable_items import ConsumableItemType
from maps.u5map import U5Map

from .interactable import Action, ActionType, Interactable
from .interactable_factory import InteractableFactory

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

    # InteractableFactory implementation: start
    def load_level(self, factory_registry: InteractableFactoryRegistry, u5map: U5Map, level_index: int):
        if u5map.location_metadata.location_index == 0:
            # There are ZERO doors in the WORLD maps, lets save a bit of loading time.
            return
        for coord in u5map.get_coord_iteration():
            if self.original_tile_id == u5map.get_tile_id(level_ix=level_index, coord=coord):
                door = DoorInstance(door_type=self, coord=coord)
                factory_registry.register_interactable(coord, door)
                print(f"[doors] registered door instance at {coord}: ",
                      f"windowed={door.door_type.original_windowed}, ",
                      f"locked={door.is_locked}, ",
                      f"magic={door.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED}")
    # InteractableFactory implementation: end

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
            return None
        if not self.is_locked:
            return None
        if self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            return ActionType.KEY_BROKE

        success = force_success or random.choice([True, False])
        if success:
            self._become_unlocked()
            return ActionType.JIMMY
        else:
            return ActionType.KEY_BROKE

    def _magic_unlock(self) -> ActionType:
        if self.is_open:
            return None
        if not self.is_locked:
            return None
        if not self.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED:
            return None
        
        self._become_unlocked()

        return ActionType.UNLOCKED

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

    def move_into(self, actor=None) -> Action:
        if self.is_open:
            return ActionType.MOVE_INTO
        else:
            return self.open()

    def open(self, actor=None) -> Action:
        if self.is_open:
            return None
        if self.is_locked:
            return ActionType.LOCKED

        self.is_open = True
        self.tile_id = DoorType.D_OPENED
        self.turns_until_close = 4

        return ActionType.OPEN
    
    def jimmy(self, actor=None) -> Action:
        return self._jimmy()
    
    def use_item_on(self, item, actor=None) -> Action:
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