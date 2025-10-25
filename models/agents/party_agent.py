# file: game/player_state.py
from datetime import datetime
from typing   import Tuple

from dark_libraries.dark_math import Coord

from models.global_location import GlobalLocation
from models.sprite import Sprite
from models.tile import Tile

from services.avatar_sprite_factory import AvatarSpriteFactory

from .npc_agent import NpcAgent
from .party_member_agent import PartyMemberAgent

transport_mode_dexterity_map = {
    0 : 15, # walk
    1 : 20, # horse
    2 : 25, # carpet
    3 : 10, # skiff
    4 : 15, # ship
    5 : 20  # sail
}

class PartyAgent(NpcAgent):

    # Injectable
    avatar_sprite_factory: AvatarSpriteFactory    

    def __init__(self):
        super().__init__()

    location_stack = list[GlobalLocation]()
    party_members  = list[PartyMemberAgent]()
    _active_member_index: int = None

    # options: walk, horse, carpet, skiff, ship
    transport_mode: int = None
    last_east_west: int = None
    last_nesw_dir: int = None
    sprite: Sprite[Tile] = None
    sprite_time_offset: float = 0.0

    # torch, light spell
    light_radius: int = None
    light_expiry: datetime = None

    #
    # Party Members
    #

    def get_active_member_index(self) -> int | None:
        return self._active_member_index

    def get_active_member(self) -> PartyMemberAgent | None:
        if self._active_member_index is None:
            return None
        else:
            return self.party_members[self._active_member_index]

    def set_active_member(self, active_member_index: int):
        self._active_member_index = active_member_index

    def add_member(self, party_member_agent: PartyMemberAgent):
        assert len(self.party_members) < 6, f"Cannot add any more members, already have {len(self.party_members)}"
        self.party_members.append(party_member_agent)

    def remove_member(self, party_member_agent: PartyMemberAgent):
        assert len(self.party_members) > 1, f"Cannot remove any more members, only have {len(self.party_members)}"
        self.party_members.append(party_member_agent)

    def get_party_members(self) -> list[PartyMemberAgent]:
        return self.party_members

    def get_party_count(self) -> int:
        return len(self.party_members)

    def get_party_member(self, party_member_index: int) -> PartyMemberAgent:
        return self.party_members[party_member_index]

    def get_party_members_in_combat(self) -> list[PartyMemberAgent]:
        return [party_member for party_member in self.party_members if party_member.is_in_combat()]

    # NPC_AGENT IMPLEMENTATION: start
    #
    @property
    def tile_id(self) -> int: ...

    @property
    def name(self) -> str: return "Quote Unquote"

    @property
    def current_tile(self) -> Tile:
        return self.sprite.get_current_frame(self.sprite_time_offset)

    @property
    def coord(self):
        return self.get_current_location().coord

    @coord.setter
    def coord(self, value: Coord[int]):
        self.location_stack[-1] = self.location_stack[-1].move_to_coord(value)

    @property
    def dexterity(self) -> int:
        transport_mode, _ = self.get_transport_state()
        return transport_mode_dexterity_map[transport_mode]
    #
    # NPC_AGENT IMPLEMENTATION: end

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
        if level_index == 256:
            level_index = 0
        elif level_index == -1:
            level_index = 255
        self.location_stack[-1] = self.location_stack[-1].move_to_level(level_index)

    def change_coord(self, coord: Coord[int]):
        old_location = self.location_stack[-1]
        new_location = self.location_stack[-1].move_to_coord(coord)
        self.location_stack[-1] = new_location
        self.log(f"DEBUG: Moved party {old_location} -> {new_location} with {self.spent_action_points} spent action points.")

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

        _, direction = self.get_transport_state()
        self.sprite = self.avatar_sprite_factory.create_player(transport_mode, direction)
        self.sprite_time_offset = self.sprite.create_random_time_offset()

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
        return self.light_expiry
