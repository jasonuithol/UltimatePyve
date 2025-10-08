from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry
from models.door_type import DoorType
from models.enums.door_type_tile_id import DoorTypeTileId


#
# TODO: THIS CLASS IS SCHEDULED FOR DEMOLITION (insane over-engineering)
#

class DoorTypeLoader(LoggerMixin):

    # injectable
    global_registry: GlobalRegistry

    def load(self):
        for original_tile_id in DoorTypeTileId:
            if original_tile_id == DoorTypeTileId.D_OPENED:
                continue
            door_type = DoorType(original_tile_id.value)
            self.global_registry.door_types.register(original_tile_id.value, door_type)
        self.log(f"Registered {len(DoorTypeTileId)} door types.")
'''
#
# main
#
if __name__ == "__main__":

    from typing import Callable
    from dark_libraries.dark_math import Coord
    from models.door_instance import DoorInstance

    registry = GlobalRegistry()
    registry._after_inject()

    loader = DoorTypeLoader()
    loader.global_registry = registry
    loader.load()

    x = 0
    def assert_state_change(original_tile_id: int, result_tile_id: int, transform: Callable):
        global registry
        global x
        door_instance: DoorInstance = registry.interactables.get(Coord(x,0))
        transform(door_instance)
        assert door_instance.tile_id == result_tile_id, f"door {original_tile_id} -> {result_tile_id}: failed test - got result of {door_instance.tile_id}."
        x = x + 1

    # unlock tests

    assert_state_change(DoorType.D_LOCKED_NORMAL,   DoorType.D_UNLOCKED_NORMAL,   lambda x: x._jimmy(force_success=True))
    assert_state_change(DoorType.D_LOCKED_WINDOWED, DoorType.D_UNLOCKED_WINDOWED, lambda x: x._jimmy(force_success=True))

    assert_state_change(DoorType.D_MAGIC_NORMAL,    DoorType.D_UNLOCKED_NORMAL,   lambda x: x._magic_unlock())
    assert_state_change(DoorType.D_MAGIC_WINDOWED,  DoorType.D_UNLOCKED_WINDOWED, lambda x: x._magic_unlock())

    assert_state_change(DoorType.D_UNLOCKED_NORMAL,   DoorType.D_OPENED, lambda x: x._open())
    assert_state_change(DoorType.D_UNLOCKED_WINDOWED, DoorType.D_OPENED, lambda x: x._open())

    print("All tests passed.")
    exit()

'''



