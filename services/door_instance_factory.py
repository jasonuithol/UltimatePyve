from data.global_registry import GlobalRegistry

from models.door_instance import DoorInstance
from models.door_type import DoorType
from models.u5_map import U5Map

from services.interactable_factory import InteractableFactory

DOOR_TYPES_DICT = dict(enumerate([
    DoorType.D_UNLOCKED_NORMAL,
    DoorType.D_UNLOCKED_WINDOWED,
    DoorType.D_LOCKED_NORMAL,
    DoorType.D_LOCKED_WINDOWED,
    DoorType.D_MAGIC_NORMAL,
    DoorType.D_MAGIC_WINDOWED,
]))

class DoorInstanceFactory(InteractableFactory):

    def __init__(self):
        pass

    # Injectable
    global_registry: GlobalRegistry

    @classmethod
    def is_door_tile(cls, tile_id: int):
        return tile_id in DOOR_TYPES_DICT.keys()

    # InteractableFactory implementation: start
    def load_level(self, u5map: U5Map, level_index: int):

        if u5map.location_metadata.location_index == 0:
            # There are ZERO doors in the WORLD maps, lets save a bit of loading time.
            return
        
        for coord in u5map.get_coord_iteration():
            
            tile_id = u5map.get_tile_id(level_ix=level_index, coord=coord)
            door_type = DOOR_TYPES_DICT[tile_id]
            if __class__.is_door_tile(tile_id):

                door = DoorInstance(door_type = door_type, coord = coord)
                self.global_registry.interactables.register(coord, door)

                print(f"[doors] registered door instance at {coord}: ",
                      f"windowed={door.door_type.original_windowed}, ",
                      f"locked={door.is_locked}, ",
                      f"magic={door.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED}")
                
    # InteractableFactory implementation: end