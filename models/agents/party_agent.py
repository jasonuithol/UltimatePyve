from datetime import datetime

from dark_libraries.dark_math import Coord, Vector2

from data.global_registry import GlobalRegistry
from models.enums.transport_mode import TRANSPORT_MODE_DEXTERITY_MAP
from models.global_location import GlobalLocation
from models.sprite import Sprite
from models.tile import Tile

from models.transport_state import TransportState

from .npc_agent import NpcAgent
from .party_member_agent import PartyMemberAgent

class PartyAgent(NpcAgent):

    #Injectable
    global_registry: GlobalRegistry

    def __init__(self):
        super().__init__(action_points = 0.0)

    location_stack = list[GlobalLocation]()
    party_members  = list[PartyMemberAgent]()
    _active_member_index: int = None

    # options: [walk, horse, carpet, skiff, ship, sail]
    # (facing north, east, west or south)
    _transport_state: TransportState = None

    sprite: Sprite[Tile] = None
    sprite_time_offset: float = None

    # torch, light spell
    light_radius: int = None
    light_expiry: datetime = None

    _multiplayer_id: int = None

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

    # NPC_AGENT IMPLEMENTATION: start
    #
    @property
    def tile_id(self) -> int:
        return self.transport_state.get_transport_tile_id()

    @property
    def name(self) -> str: return self.party_members[0].name

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
        return TRANSPORT_MODE_DEXTERITY_MAP[self._transport_state.transport_mode]

    @property
    def slept(self) -> bool:
        return False
    #
    # NPC_AGENT IMPLEMENTATION: end


    @property
    def multiplayer_id(self) -> str:
        assert self._multiplayer_id, "Cannot access multiplayer_id before it is set."
        return self._multiplayer_id

    def set_multiplayer_id(self, remote_multiplayer_id: str = None):
        if remote_multiplayer_id is None:
            # server mode
            self._multiplayer_id = str(id(self))
        else:
            # client mode
            self._multiplayer_id = remote_multiplayer_id

    def clear_multiplayer_id(self):
        self._multiplayer_id = None

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

    def apply_move_offset(self, move_offset: Vector2[int]):
        x, y = self.coord + move_offset
        self.change_coord(Coord(x,y))
        self.transport_state.apply_move_offset(move_offset)
        self._update_sprite()

    def get_current_location(self) -> GlobalLocation:
        return self.location_stack[-1]

    # 1 = over/under world
    # 2 = town, dungeon, over/under world combat
    # 3 = dungeon room (combat), dungeon corridor combat, town combat
    def get_location_depth(self) -> int:
        return len(self.location_stack)

    @property
    def location(self) -> GlobalLocation:
        return self.location_stack[-1]

    #
    # Transport state.
    #
    @property
    def transport_state(self) -> TransportState:
        return self._transport_state
    
    @transport_state.setter
    def transport_state(self, value: TransportState):
        self._transport_state = value
        self._update_sprite()

    def _update_sprite(self):
        sprite = self.global_registry.sprites.get(self.transport_state.get_transport_tile_id())
        assert sprite, f"Could not obtain sprite from transport_state={self.transport_state}"
        self.sprite = sprite
        if self.sprite_time_offset is None:
            self.sprite_time_offset = sprite.create_random_time_offset()

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
