# file: game/doors.py
from typing import Callable

from dark_libraries.dark_math import Coord

from .door_type_and_door_instance import DoorType
from .interactable_factory_registry import InteractableFactoryRegistry

class DoorTypeFactory:

    # injectable
    interactable_factory_registry: InteractableFactoryRegistry

    def register_interactable_factories(self):
            for original_tile_id in [
                DoorType.D_MAGIC_NORMAL,
                DoorType.D_MAGIC_WINDOWED,

                DoorType.D_UNLOCKED_NORMAL,
                DoorType.D_UNLOCKED_WINDOWED,

                DoorType.D_LOCKED_NORMAL,
                DoorType.D_LOCKED_WINDOWED,
            ]:
                door_type = DoorType(original_tile_id)
                self.interactable_factory_registry.register_interactable_factory(
                     tile_id = door_type.original_tile_id, 
                     factory = door_type
                )

#
# main
#
if __name__ == "__main__":

    registry = InteractableFactoryRegistry()
    registry._after_inject()

    factory = DoorTypeFactory()
    factory.interactable_factory_registry = registry
    factory.register_interactable_factories()

    x = 0
    def assert_state_change(original_tile_id: int, result_tile_id: int, transform: Callable):
        global registry
        global x
        door_instance = registry.get_interactable(original_tile_id, Coord(x,0))
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




