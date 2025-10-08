from dark_libraries.custom_decorators import immutable

from models.enums.door_type_tile_id import DoorTypeTileId

@immutable
class DoorType:

    # Original lock states
    L_UNLOCKED     = 0
    L_KEY_LOCKED   = 1
    L_MAGIC_LOCKED = 2

    def __init__(self, tile_id: int):
        # Set Permanent state
        self.original_tile_id: int  = tile_id

        self.original_windowed: bool = (
            tile_id in [
                DoorTypeTileId.D_UNLOCKED_WINDOWED.value, 
                DoorTypeTileId.D_LOCKED_WINDOWED.value, 
                DoorTypeTileId.D_MAGIC_WINDOWED.value
            ]
        )

        if tile_id in [DoorTypeTileId.D_UNLOCKED_NORMAL.value, DoorTypeTileId.D_UNLOCKED_WINDOWED.value]:
            self.original_lock_type = DoorType.L_UNLOCKED
            return
        if tile_id in [DoorTypeTileId.D_LOCKED_NORMAL.value,   DoorTypeTileId.D_LOCKED_WINDOWED.value]:
            self.original_lock_type = DoorType.L_KEY_LOCKED
            return
        if tile_id in [DoorTypeTileId.D_MAGIC_NORMAL.value,    DoorTypeTileId.D_MAGIC_WINDOWED.value]:
            self.original_lock_type = DoorType.L_MAGIC_LOCKED
            return

        assert False, f"Unknown original tile_id for doors: {tile_id}"