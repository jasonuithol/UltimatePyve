from dark_libraries.custom_decorators import immutable

@immutable
class DoorType:

    # Tile types.
    D_OPENED            = 68

    D_UNLOCKED_NORMAL   = 184
    D_UNLOCKED_WINDOWED = 186

    D_LOCKED_NORMAL     = 185
    D_LOCKED_WINDOWED   = 187

    D_MAGIC_NORMAL      = 151
    D_MAGIC_WINDOWED    = 152

    # Original lock states
    L_UNLOCKED     = 0
    L_KEY_LOCKED   = 1
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

        assert False, f"Unknown original tile_id for doors: {tile_id}"