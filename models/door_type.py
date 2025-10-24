
from models.enums.door_type_tile_id import DoorTypeTileId

class DoorType(tuple):

    # Original lock states
    L_UNLOCKED     = 0
    L_KEY_LOCKED   = 1
    L_MAGIC_LOCKED = 2

    def __new__(cls, tile_id: int):
        # Set Permanent state
        original_tile_id: int  = tile_id

        original_windowed: bool = (
            tile_id in [
                DoorTypeTileId.D_UNLOCKED_WINDOWED.value, 
                DoorTypeTileId.D_LOCKED_WINDOWED.value, 
                DoorTypeTileId.D_MAGIC_WINDOWED.value
            ]
        )

        if tile_id in [DoorTypeTileId.D_UNLOCKED_NORMAL.value, DoorTypeTileId.D_UNLOCKED_WINDOWED.value]:
            original_lock_type = DoorType.L_UNLOCKED
        elif tile_id in [DoorTypeTileId.D_LOCKED_NORMAL.value,   DoorTypeTileId.D_LOCKED_WINDOWED.value]:
            original_lock_type = DoorType.L_KEY_LOCKED
        elif tile_id in [DoorTypeTileId.D_MAGIC_NORMAL.value,    DoorTypeTileId.D_MAGIC_WINDOWED.value]:
            original_lock_type = DoorType.L_MAGIC_LOCKED
        else:
            assert False, f"Unknown original tile_id for doors: {tile_id}"

        return tuple.__new__(cls, (original_tile_id, original_windowed, original_lock_type))
    
    @property
    def original_tile_id(self) -> int:
        return self[0]
    
    @property
    def original_windowed(self) -> bool:
        return self[1]

    @property
    def original_lock_type(self) -> int:
        return self[2]
