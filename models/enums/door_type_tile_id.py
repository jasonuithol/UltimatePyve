from enum import Enum
from models.door_type import DoorType

class DoorTypeTileId(Enum):
    DoorType.D_MAGIC_NORMAL
    DoorType.D_MAGIC_WINDOWED

    DoorType.D_UNLOCKED_NORMAL
    DoorType.D_UNLOCKED_WINDOWED

    DoorType.D_LOCKED_NORMAL
    DoorType.D_LOCKED_WINDOWED