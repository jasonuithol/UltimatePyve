from typing import NamedTuple
from dark_libraries.dark_math import Coord
from models.agents.multiplayer_party_agent import MultiplayerPartyAgent
from models.agents.party_agent import PartyAgent
from models.global_location import GlobalLocation

def _get_coord(self):
    return Coord(self.x, self.y)

def _get_location(self):
    return GlobalLocation(
        self.location_index,
        self.level_index,
        _get_coord(self)
    )

class ConnectRequest(NamedTuple):
    name: str
    dexterity: int

    location_index: int
    level_index: int
    x: int 
    y: int

    get_coord = _get_coord
    get_location = _get_location

    def create_multiplayer_party_agent(self):
        return MultiplayerPartyAgent(
            name      = self.name,
            dexterity = self.dexterity,
            location  = self.get_location()
        )

    @classmethod
    def from_agent(cls, agent: PartyAgent):
        return cls(
            name = agent.name,
            dexterity = agent.dexterity,

            location_index = agent.location.location_index,
            level_index    = agent.location.level_index,
            x = agent.location.coord.x,
            y = agent.location.coord.y
        )

class ConnectAccept(NamedTuple):
    multiplayer_id: str
    x: int
    y: int

    get_coord = _get_coord

    @classmethod
    def from_agent(cls, agent: MultiplayerPartyAgent):
        return cls(
            multiplayer_id = agent.multiplayer_id,
            x = agent.location.coord.x,
            y = agent.location.coord.y
        )

    def update_agent(self, agent: PartyAgent):
        agent.set_multiplayer_id(self.multiplayer_id)
        agent.change_coord(self.get_coord())

class PlayerJoin(NamedTuple):
    name: str
    dexterity: int
    multiplayer_id: str

    location_index: int
    level_index: int
    x: int 
    y: int

    get_coord = _get_coord
    get_location = _get_location

    @classmethod
    def from_agent(cls, agent: PartyAgent | MultiplayerPartyAgent):
        return cls(
            name = agent.name,
            dexterity = agent.dexterity,
            multiplayer_id = agent.multiplayer_id,

            location_index = agent.location.location_index,
            level_index    = agent.location.level_index,
            x = agent.location.coord.x,
            y = agent.location.coord.y
        )

    def create_multiplayer_party_agent(self):
        return MultiplayerPartyAgent(
            name      = self.name,
            dexterity = self.dexterity,
            location  = self.get_location(),
            remote_multiplayer_id = self.multiplayer_id
        )
    
class LocationUpdate(NamedTuple):
    multiplayer_id: str

    location_index: int
    level_index: int
    x: int
    y: int

    get_coord = _get_coord
    get_location = _get_location

    @classmethod
    def from_agent(cls, agent: PartyAgent | MultiplayerPartyAgent):
        return cls(
            multiplayer_id = agent.multiplayer_id,

            location_index = agent.location.location_index,
            level_index    = agent.location.level_index,
            x = agent.location.coord.x,
            y = agent.location.coord.y
        )

    def update_agent(self, agent: PartyAgent | MultiplayerPartyAgent):
        agent.location = self.get_location()
