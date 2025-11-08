from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.agents.multiplayer_party_agent import MultiplayerPartyAgent
from models.agents.party_agent             import PartyAgent
from models.agents.combat_agent            import CombatAgent
from models.enums.npc_tile_id import NpcTileId
from models.multiplayer_protocol import ConnectAccept, ConnectRequest, ConnectTerminate, LocationUpdate, PlayerJoin, PlayerLeave

class MultiplayerMessageFactory(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry
    party_agent:     PartyAgent

    # =======================================
    #
    #              OUTGOING
    #
    # =======================================

    def connect_request(self) -> ConnectRequest:

        agent    = self.party_agent
        location = agent.location
        coord    = location.coord

        return ConnectRequest(
            name      = agent.name,
            tile_id   = agent.tile_id,
            dexterity = agent.dexterity,

            location_index = location.location_index,
            level_index    = location.level_index,
            x              = coord.x,
            y              = coord.y
        )

    def connect_accept(self, agent: MultiplayerPartyAgent) -> ConnectAccept:
        return ConnectAccept(
            multiplayer_id = agent.multiplayer_id,
            x = agent.location.coord.x,
            y = agent.location.coord.y
        )

    def connect_terminate(self) -> ConnectTerminate:
        return ConnectTerminate()

    def player_join(self, agent: PartyAgent | MultiplayerPartyAgent | CombatAgent) -> PlayerJoin:

        if isinstance(agent, CombatAgent):
            location = self.party_agent.location
        else:
            location = agent.location

        coord = agent.coord

        return PlayerJoin(
            name           = agent.name,
            tile_id        = agent.tile_id,
            dexterity      = agent.dexterity,
            multiplayer_id = agent.multiplayer_id,

            location_index = location.location_index,
            level_index    = location.level_index,
            x              = coord.x,
            y              = coord.y
        )

    def player_leave(self) -> PlayerLeave:
        return PlayerLeave(
            multiplayer_id = self.party_agent.multiplayer_id
        )

    def location_update(self, agent: PartyAgent | MultiplayerPartyAgent | CombatAgent) -> LocationUpdate:

        if isinstance(agent, CombatAgent):
            location = self.party_agent.location
        else:
            location = agent.location
            
        coord = agent.coord

        return LocationUpdate(
            multiplayer_id = agent.multiplayer_id,

            location_index = location.location_index,
            level_index    = location.level_index,
            x              = coord.x,
            y              = coord.y
        )

    # =======================================
    #
    #              INCOMING
    #
    # =======================================
    
    def create_multiplayer_party_agent(self, message: ConnectRequest | PlayerJoin) -> MultiplayerPartyAgent:

        if isinstance(message, ConnectRequest):
            remote_multiplayer_id: int = None
        elif isinstance(message, PlayerJoin):
            remote_multiplayer_id = message.multiplayer_id
        else:
            assert False, f"Unknown message: {message.__class__.__name__}"

        sprite = self.global_registry.sprites.get(message.tile_id)
        if sprite is None:
            self.log(f"WARNING: Could not obtain sprite for tile_id={message.tile_id}")
            sprite = self.global_registry.sprites.get(NpcTileId.JESTER.value)

        return MultiplayerPartyAgent(
            name      = message.name,
            tile_id   = message.tile_id,
            sprite    = sprite,
            dexterity = message.dexterity,
            location  = message.get_location(),

            remote_multiplayer_id = remote_multiplayer_id
        )
    
    def update_agent(self, agent: PartyAgent | MultiplayerPartyAgent, message: ConnectAccept | LocationUpdate):

        if isinstance(agent, PartyAgent) and isinstance(message, ConnectAccept):
            agent.set_multiplayer_id(message.multiplayer_id)
            agent.change_coord(message.get_coord())

        elif isinstance(agent, MultiplayerPartyAgent) and isinstance(message, LocationUpdate):
            agent.location = message.get_location()

        else:
            assert False, f"Unknown agent/message combination: {agent.__class__.__name__}|{message.__class__.__name__}"        


