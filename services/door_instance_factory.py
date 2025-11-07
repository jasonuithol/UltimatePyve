from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.door_instance import DoorInstance
from models.door_type import DoorType
from models.global_location import GlobalLocation
from models.u5_map import U5Map
from models.enums.door_type_tile_id import DoorTypeTileId

#
# TODO: THIS CLASS IS SCHEDULED FOR DEMOLITION (insane overengineering)
#

#
# TODO: Just add some custom tiles that replicate either the tiled-floor or various unlocked doors hence:
# OPENED_DOOR_NORMAL, OPENED_DOOR_KEYED, OPENED_DOOR_MAGIC = tiled-floor (68)
# UNLOCKED_DOOR_KEYED, UNLOCKED_DOOR_MAGIC = UNLOCKED_DOOR_NORMAL
# etc - and make WINDOWED variants of all.
#

class DoorInstanceFactory(LoggerMixin, DarkEventListenerMixin):

    def __init__(self):
        super().__init__()
        self.log("WARNING: This class is scheduled for demolition")

    # Injectable
    global_registry: GlobalRegistry

    @classmethod
    def is_door_tile(cls, tile_id: int):
        return tile_id in {door_type.value for door_type in DoorTypeTileId if door_type != DoorTypeTileId.D_OPENED}

    # DarkEventListenerMixin implementation: start
    def loaded(self, party_location: GlobalLocation):
        self.level_changed(party_location)

    def level_changed(self, party_location: GlobalLocation):

        self.log(f"DEBUG: Unregistering {len(self.global_registry.interactables)} door instances.")
        self.global_registry.interactables.clear()

        if party_location.location_index == 0:
            # There are ZERO doors in the WORLD maps, lets save a bit of loading time.
            return
        
        u5_map: U5Map = self.global_registry.maps.get(party_location.location_index)
        if u5_map is None:
            self.log("WARNING: Skipping registration of door instances.")
            # is a combat map or dungeon room.  NOT IMPLEMENTED - WAIT UNTIL REPLACEMENT
            return

        for coord in u5_map.get_coord_iteration():
            
            tile_id = u5_map.get_tile_id(level_index = party_location.level_index, coord = coord)

            if __class__.is_door_tile(tile_id):

                door_type = self.global_registry.door_types.get(tile_id)
                assert not door_type is None, f"Did not get a door_type for tile_id={tile_id}"

                door = DoorInstance(door_type = door_type, coord = coord)
                self.global_registry.interactables.register(coord, door)

                self.log(
                    f"Registered door instance at {coord}: "
                    +     
                    f"windowed={door.door_type.original_windowed}, "
                    +
                    f"locked={door.is_locked}, "
                    +
                    f"magic={door.door_type.original_lock_type == DoorType.L_MAGIC_LOCKED}"
                )
    def pass_time(self, party_location: GlobalLocation):
        for interactable in self.global_registry.interactables.values():
            interactable.pass_time(party_location)
    # DarkEventListenerMixin implementation: end