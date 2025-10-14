from dark_libraries.dark_math import Coord, Vector2

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.global_location import GlobalLocation
from models.interactable import Interactable
from models.move_into_result import MoveIntoResult
from models.terrain import Terrain
from models.u5_map import U5Map
from services.npc_service import NpcService

#
# outcomes:
# a) move coord
# b) blocked
# c) up/down
# d) enter/exit map
#
class MoveOutcome:
    def __init__(self,
        success:   bool           = False,
        blocked:   bool           = False,
        move_up:   bool           = False,
        move_down: bool           = False,
        enter_map: GlobalLocation = None,
        exit_map:  bool           = False
    ):
        self.success   = success
        self.blocked   = blocked
        self.move_up   = move_up
        self.move_down = move_down
        self.enter_map = enter_map
        self.exit_map  = exit_map

    def __str__(self) -> str:
        return self.__class__.__name__ + ": " + ", ".join([f"{n}={v}" for n,v in vars(self).items()])
            

class MoveController(LoggerMixin):

    global_registry: GlobalRegistry
    npc_service: NpcService

    def move(self, current_location: GlobalLocation, move_offset: Vector2, transport_mode_name: str) -> MoveOutcome:

        current_map: U5Map = self.global_registry.maps.get(current_location.location_index)
        target_location = current_location + move_offset

        # Handle out-of-bounds.
        if current_map.location_index == 0:
            # When in the overworld/underworld, wrap the coord because it's a globe.
            target_location = target_location.move_to_coord(current_map.get_wrapped_coord(target_location.coord))
        else:
            # When in a town/dungeon room/combat map etc, going out-of-bounds means exiting the map
            if not current_map.get_size().is_in_bounds(target_location.coord):
                return MoveOutcome(exit_map=True)

        # This may perform a "move_into" operation on an interactable.
        move_into_result: MoveIntoResult = self._try_move_into(current_location, target_location.coord, transport_mode_name)
        got_blocked = (not move_into_result.traversal_allowed) and (not move_into_result.alternative_action_taken)
        if not move_into_result.traversal_allowed:
            if got_blocked:
                self.log(f"DEBUG: Blocking move to {target_location.coord}: _try_move_into() failed")
            return MoveOutcome(blocked=got_blocked)

        # handle bumping into NPCs.
        #---------------------------------------------------------------------------------
        # TODO: This will need to track every party member
        if target_location.coord in self.npc_service.get_occupied_coords():
        #---------------------------------------------------------------------------------
            self.log(f"DEBUG: Blocking move to {target_location.coord}: _get_occupied_coords() {self.npc_service.get_occupied_coords()}")
            return MoveOutcome(blocked=True)


        target_tile_id = current_map.get_tile_id(current_location.level_index, target_location.coord)
        target_terrain: Terrain = self.global_registry.terrains.get(target_tile_id)

        # entry points
        if target_terrain.entry_point == True:
            new_location: GlobalLocation = self.global_registry.entry_triggers.get(target_location)
            return MoveOutcome(enter_map = new_location)

        #
        # TODO: This could be entering the over or underworld from a dungeon room
        #
        # map level change checks.
        new_level_index = current_location.level_index

        # ladders                
        if target_terrain.move_up == True:
            new_level_index = target_location.level_index + 1

        if target_terrain.move_down == True:
            new_level_index = target_location.level_index - 1

        # stairs
        if target_terrain.stairs == True:
            # NOTE: This is just a guess, but seems to be working out ok.
            # Stairs always lead from the default spawn level to the one above it, and then back again.
            if current_location.level_index == current_map.default_level_index:
                new_level_index = current_map.default_level_index + 1
            else:
                new_level_index = current_map.default_level_index

        # update level if changed.
        if new_level_index > current_location.level_index:
            return MoveOutcome(move_up=True)
        elif new_level_index < current_location.level_index:
            return MoveOutcome(move_down=True)
        else:
            self.log(f"DEBUG: Move to {target_location} succeeded.")
            return MoveOutcome(success=True)
        
    def _try_move_into(self, current_location: GlobalLocation, target: Coord, transport_mode_name: str) -> MoveIntoResult:

        interactable: Interactable = self.global_registry.interactables.get(target)      
        if interactable:

            #
            # NOTE: This might result in a door opening, or a piece of loot being taken, rather than actual movement.
            #
            return interactable.move_into()

        # It's just regular terrain.
        current_map: U5Map  = self.global_registry.maps.get(current_location.location_index)
        target_tile_id: int = current_map.get_tile_id(current_location.level_index, target)
        terrain: Terrain    = self.global_registry.terrains.get(target_tile_id)

        return MoveIntoResult(
            traversal_allowed = terrain.can_traverse(transport_mode_name),
            alternative_action_taken = False
        )    




