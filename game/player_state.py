# file: game/player_state.py
from typing import Optional, Tuple

from dark_libraries.custom_decorators import auto_init
from dark_libraries.dark_math import Coord, Vector2

from game.interactable import InteractionResult
from game.map_transitions import get_entry_trigger
from game.u5map import U5Map
from game.world_state import WorldState

from loaders.location import LocationLoader

from terrain import get_transport_modes, can_traverse

# TODO: Once testing is finished, delete these.
from loaders.overworld import Britannia, load_britannia
from loaders.underworld import UnderWorld, load_underworld
    
#
# An immutable state.  transitions return a cloned, modified copy of current state
#
class PlayerState:

    # Injectable
    world_state: WorldState
    location_loader: LocationLoader

    # either "britannia" or "underworld"
    outer_map: U5Map = None          
    outer_coord: Coord = None

    inner_map: Optional[U5Map] = None
    inner_map_level: Optional[int] = None
    inner_coord: Optional[Coord] = None

    # options: walk, horse, carpet, skiff, ship
    transport_mode: int = None
    last_east_west: int = None
    last_nesw_dir: int = None

    def set_outer_position(self, u5Map: U5Map, coord: Coord):
        self.outer_map = u5Map
        self.outer_coord = coord

    def set_transport_state(self, transport_mode: int, last_east_west: int, last_nesw_dir: int):
        self.transport_mode = transport_mode
        self.last_east_west = last_east_west
        self.last_nesw_dir = last_nesw_dir

    def is_in_outer_map(self) -> bool:
        return self.inner_map is None

    def get_current_position(self) -> Tuple[U5Map, int, Coord]:
        if self.is_in_outer_map():
            return self.outer_map, 0, self.outer_coord
        else:
            return self.inner_map, self.inner_map_level, self.inner_coord

    def get_current_transport_info(self) -> Tuple[int, int]:
        if self.transport_mode == 0:
            direction = 0 # no one cares.
        elif self.transport_mode < 3:
            direction = self.last_east_west
        else:
            direction = self.last_nesw_dir

        return self.transport_mode, direction

    def _can_traverse(self, target: Coord) -> bool:
        transport_mode = get_transport_modes()[self.transport_mode]
        current_map, current_level, _ = self.get_current_position()
        target_tile_id = current_map.get_tile_id(current_level, target)
        interactable = self.world_state.get_interactable(target_tile_id, target)      
        if interactable:
            result = interactable.move_into()
            return result.success
        return can_traverse(transport_mode, target_tile_id)

    #
    # Internal State transitions
    #

    def _on_changing_map(self) -> None:
        self.world_state.clear_interactables()

    def _move_to_inner_map(self, u5map: U5Map) -> InteractionResult:
        self.inner_map = u5map
        self.inner_map_level = u5map.location_metadata.default_level
        self.inner_coord = Coord(
            (u5map.size_in_tiles.w - 1) // 2,
            (u5map.size_in_tiles.h - 2)
        )
        self._on_changing_map()
        return InteractionResult.ok(f"Entered {u5map.name}")

    def _return_to_outer_map(self) -> InteractionResult:
        msg = f"Exited {self.inner_map.name}"

        self.inner_map = None
        self.inner_map_level = None
        self.inner_coord = None
        self._on_changing_map()
        return InteractionResult.ok(msg)

    #
    # Player driven State transitions
    #

    def move(self, value: Vector2) -> InteractionResult:

        #
        # Check map transitions
        #

        if self.is_in_outer_map():
            target = self.outer_coord.add(value)
            target = self.outer_map.get_wrapped_coord(target)

            # Check traversability before transitions.
            # A ship cannot enter a town, for example, so we must forbid it here.
            if not self._can_traverse(target):
                return InteractionResult.error("Blocked")
            
            # Check map transitions
            trigger_index = get_entry_trigger(target)
            if not trigger_index is None:
                inner_map = self.location_loader.load_location_map(trigger_index)
                # always succeeds.
                return self._move_to_inner_map(inner_map)

            self.outer_coord = target

        else:
            target = self.inner_coord.add(value)
            if not self.inner_map.is_in_bounds(target):
                # always succeeds.
                return self._return_to_outer_map()

            if not self._can_traverse(target):
                return InteractionResult.error("Blocked")
            
            self.inner_coord = target

        if value.x == 1:
            # east
            self.last_east_west = 0
            self.last_nesw_dir = 1
        elif value.x == -1:
            # west
            self.last_east_west = 1
            self.last_nesw_dir = 3
        elif value.y == 1:
            # south
            self.last_nesw_dir = 2
        elif value.y == -1:
            # north
            self.last_nesw_dir = 0

        return InteractionResult.ok()

    #
    # Testing only
    #

    def switch_outer_map(self) -> InteractionResult:
        if self.outer_map.name == "BRITANNIA":
            self.outer_map = load_underworld()
        else:
            self.outer_map = load_britannia()
        return InteractionResult.ok()
    
    def rotate_transport(self) -> InteractionResult:

        self.transport_mode = (self.transport_mode + 1) % len(get_transport_modes())

        # forbid turning into a ship on land, for example.
        _, _, target = self.get_current_position()
        if not self._can_traverse(target):
            return InteractionResult.error()
        
        return InteractionResult.ok()

