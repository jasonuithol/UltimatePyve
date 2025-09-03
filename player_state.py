# file: player_state.py
from dataclasses import dataclass
from typing import Optional, Self

from interactable import Interactable
from u5map import U5Map
from dark_math import Coord, Vector2
from terrain import get_transport_modes, can_traverse
from map_transitions import get_entry_trigger
from world_state import WorldState

from loaders.location import load_location_map
from loaders.overworld import load_britannia
from loaders.underworld import load_underworld
    
#
# An immutable state.  transitions return a cloned, modified copy of current state
#
@dataclass
class PlayerState:

    world_state: WorldState

    # either "britannia" or "underworld"
    outer_map: U5Map          
    outer_coord: Coord

    inner_map: Optional[U5Map] = None
    inner_map_level: int = None
    inner_coord: Optional[Coord] = None

    # options: walk, horse, carpet, skiff, ship
    transport_mode: int = 0 # walk
    last_east_west: int = 0 # east
    last_nesw_dir: int = 1 # east

    def is_in_outer_map(self):
        return self.inner_map is None

    def get_current_position(self):
        if self.is_in_outer_map():
            return self.outer_map, 0, self.outer_coord
        else:
            return self.inner_map, self.inner_map_level, self.inner_coord

    def get_current_transport_info(self):
        if self.transport_mode == 0:
            direction = 0 # no one cares.
        elif self.transport_mode < 3:
            direction = self.last_east_west
        else:
            direction = self.last_nesw_dir

        return self.transport_mode, direction

    def _can_traverse(self, target: Coord):
        transport_mode = get_transport_modes()[self.transport_mode]
        current_map, current_level, _ = self.get_current_position()
        target_tile_id = current_map.get_tile_id(current_level, target.x, target.y)
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

    def _move_to_inner_map(self, u5map: U5Map) -> Self:
        self.inner_map = u5map
        self.inner_map_level = u5map.location_metadata.default_level
        self.inner_coord = Coord(
            (u5map.size_in_tiles.w - 1) // 2,
            (u5map.size_in_tiles.h - 2)
        )
        self._on_changing_map()
        return self

    def _return_to_outer_map(self) -> Self:
        self.inner_map = None
        self.inner_map_level = None
        self.inner_coord = None
        self._on_changing_map()
        return self

    #
    # Player driven State transitions
    #

    def move(self, value: Vector2) -> Self:

        #
        # Check map transitions
        #

        if self.is_in_outer_map():
            target = self.outer_coord.add(value)
            target = self.outer_map.get_wrapped_coord(target)

            # Check traversability before transitions.
            # A ship cannot enter a town, for example, so we must forbid it here.
            if not self._can_traverse(target):
                return None
            
            # Check map transitions
            trigger_index = get_entry_trigger(target)
            if not trigger_index is None:
                inner_map = load_location_map(trigger_index)
                # always succeeds.
                return self._move_to_inner_map(inner_map)

            self.outer_coord = target

        else:
            target = self.inner_coord.add(value)
            if not target.is_in_bounds(self.inner_map.size_in_tiles):
                # always succeeds.
                return self._return_to_outer_map()

            if not self._can_traverse(target):
                return None
            
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

        return self

    #
    # Testing only
    #

    def switch_outer_map(self) -> Self:
        if self.outer_map.name == "BRITANNIA":
            self.outer_map = load_underworld()
        else:
            self.outer_map = load_britannia()
        return self
    
    def rotate_transport(self) -> Self:

        self.transport_mode = (self.transport_mode + 1) % len(get_transport_modes())

        # forbid turning into a ship on land, for example.
        _, _, target = self.get_current_position()
        if not self._can_traverse(target):
            return None
        
        return self

