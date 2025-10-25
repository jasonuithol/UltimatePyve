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
        self.log("WARNING: This class is scheduled for demolition")
        for original_tile_id in DoorTypeTileId:
            if original_tile_id == DoorTypeTileId.D_OPENED:
                continue
            door_type = DoorType(original_tile_id.value)
            self.global_registry.door_types.register(original_tile_id.value, door_type)
        self.log(f"Registered {len(self.global_registry.door_types)} door types.")





