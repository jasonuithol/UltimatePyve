# file: game/player_state.py
from datetime import datetime
from typing   import Tuple

from dark_libraries.dark_math import Coord

from models.global_location import GlobalLocation

class PartyState:

    location_stack: list[GlobalLocation] = []

    # options: walk, horse, carpet, skiff, ship
    transport_mode: int = None
    last_east_west: int = None
    last_nesw_dir: int = None

    # torch, light spell
    light_radius: int = None
    light_expiry: datetime = None

    #
    # Location
    #
    def push_location(self, location: GlobalLocation):
        self.location_stack.append(location)

    def pop_location(self):
        self.location_stack.pop()

    # good for resurrecting at the castle, moongate travel from towns (if that's possible)
    def clear_locations(self):
        self.location_stack.clear()

    def change_level(self, level_index: int):
        self.location_stack[-1].level_index = level_index

    def change_coord(self, coord: Coord):
        self.location_stack[-1].coord = coord

    def get_current_location(self) -> GlobalLocation:
        return self.location_stack[-1]

    # 1 = over/under world
    # 2 = town, dungeon, over/under world combat
    # 3 = dungeon room (combat), dungeon corridor combat, town combat
    def get_location_depth(self) -> int:
        return len(self.location_stack)

    #
    # Transport mode.
    #
    def set_transport_state(self, transport_mode: int, last_east_west: int, last_nesw_dir: int):
        self.transport_mode = transport_mode
        self.last_east_west = last_east_west
        self.last_nesw_dir = last_nesw_dir

    def get_transport_state(self) -> Tuple[int, int]:
        assert not self.transport_mode is None, "Must call set_transport_state first."
        if self.transport_mode == 0:
            direction = 0 # no one cares.
        elif self.transport_mode < 3:
            direction = self.last_east_west
        else:
            direction = self.last_nesw_dir
        return self.transport_mode, direction

    #
    # Light radius
    #
    def set_light(self, radius: int, expiry: datetime):
        self.light_radius = radius
        self.light_expiry = expiry

    def get_light_radius(self) -> int:
        return self.light_radius

    def get_light_expiry(self) -> datetime:
        return self.light_radius
