from typing import NamedTuple

from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_socket_network import DarkSocketClient, DarkSocketServer
from dark_libraries.dark_tuple_network_protocol import DarkNamedTupleProtocol
from dark_libraries.logging import LoggerMixin

import models.multiplayer_protocol
from models.agents.multiplayer_party_agent import MultiplayerPartyAgent
from models.agents.party_agent import PartyAgent
from models.multiplayer_protocol import ConnectAccept, ConnectRequest, ConnectTerminate, LocationUpdate, PlayerJoin, PlayerLeave

from services.info_panel_service import InfoPanelService
from services.npc_service import NpcService

# If you're changing one of these, you may need to change the other
ProtocolFormat     = NamedTuple
ProtocolDefinition = models.multiplayer_protocol

class MultiplayerService(LoggerMixin, DarkEventListenerMixin):

    npc_service: NpcService
    party_agent: PartyAgent
    info_panel_service: InfoPanelService

    def __init__(self):
        super().__init__()
        self.server: DarkSocketServer[ProtocolFormat] = None
        self.client: DarkSocketClient[ProtocolFormat] = None
        self.client_agents = dict[str, MultiplayerPartyAgent]()
        self.protocol = DarkNamedTupleProtocol(ProtocolDefinition)

    # =====================================
    #
    #               SERVER
    #
    # =====================================

    def start_hosting(self):
        assert (not self.server) and (not self.client), f"Cannot start hosting: server={self.server}, self={self.client}"

        self.server: DarkSocketServer[ProtocolFormat] = DarkSocketServer[ProtocolFormat](self.protocol)
        self.server.launch()
        self.party_agent.set_multiplayer_id()
        self.party_agent.party_members[0]._character_record.name = "SERVER"
        self.info_panel_service.update_party_summary()

    def read_client_updates(self):

        for network_id, named_tuple in self.server.read():
            try:
                if isinstance(named_tuple, ConnectRequest):
                    self._connect_new_client(network_id, named_tuple)

                elif isinstance(named_tuple, LocationUpdate):
                    self._accept_location_update(named_tuple)

                elif isinstance(named_tuple, PlayerLeave):
                    self._accept_player_leave(named_tuple, network_id)

            except Exception as e:
                self.log(f"ERROR: Error whilst processing message ({named_tuple}) from client {network_id}: {e}")

    def write_client_updates(self):

        # Send your (the host)'s location to all remote players
        self.server.write(LocationUpdate.from_agent(self.party_agent))

        # Send everyone's location to all remote players
        player_location_message_grams = [
            LocationUpdate.from_agent(agent)
            for agent in self.client_agents.values()
        ]
        for message_gram in player_location_message_grams:
            self.server.write(message_gram)

    def _connect_new_client(self, network_id: str, connect_request: ConnectRequest):

        #
        # TODO: Check if there's another registered player at this location (overworld)
        #
        agent = connect_request.create_multiplayer_party_agent()

        self.client_agents[agent.multiplayer_id] = agent
        self._update_multiplayer_npc_registration()

        # Update the new client with it's multiplayer_id and it's spawn location (might be different to requested spawn location)
        connect_accept_message_gram = ConnectAccept.from_agent(agent)
        self.server.write_to(network_id, connect_accept_message_gram)

        # Tell the new guy about all the other people in the lobby
        for other_agent in self.client_agents.values():
            self.server.write(PlayerJoin.from_agent(other_agent))

        # Tell the new guy about ME
        self.server.write(PlayerJoin.from_agent(self.party_agent))

        self.log(f"Player '{agent.name}' has joined with network_id={network_id}, multiplayer_id={agent.multiplayer_id}")


    # ======================================================
    #
    #                       CLIENT
    #
    # ======================================================

    def connect_to_host(self, host: str, port: int):
        assert (not self.server) and (not self.client), f"Cannot connect to host: server={self.server}, client={self.client}"
        self.client: DarkSocketClient[ProtocolFormat] = DarkSocketClient[ProtocolFormat](host, port, self.protocol)
        self.client.write(ConnectRequest.from_agent(self.party_agent))

    def read_server_updates(self):

        if self.party_agent._multiplayer_id is None:
            self._read_connect_accept()
            return

        for named_tuple in self.client.read():
            
            if isinstance(named_tuple, PlayerJoin):
                self._accept_player_join(named_tuple)
                
            elif isinstance(named_tuple, PlayerLeave):
                self._accept_player_leave(named_tuple)

            elif isinstance(named_tuple, LocationUpdate):
                self._accept_location_update(named_tuple)

            elif isinstance(named_tuple, ConnectTerminate):
                self._accept_connect_terminate()

    def write_server_updates(self):

        message_gram = LocationUpdate.from_agent(self.party_agent)
        self.client.write(message_gram)

    def _read_connect_accept(self):
        for named_tuple in self.client.read():
            if isinstance(named_tuple, ConnectAccept):
                named_tuple.update_agent(self.party_agent)
                self.log(f"Connnection to server accepted, multiplayer_id={named_tuple.multiplayer_id}")
                return
        self.log(f"WARNING: Have not received ConnectAccept, so no multiplayer_id is yet assigned.")

    def _accept_connect_terminate(self):
        self.log(f"Server terminating connection, removing remote players and closing client connection.")
        for agent in self.client_agents.values():
            self.npc_service.remove_npc(agent)
        self.client_agents.clear()
        self.client.close()
        self.client = None

    # ===============================
    #
    # SHARED
    #
    # ===============================

    def _accept_player_join(self, player_join: PlayerJoin):

        if player_join.multiplayer_id != self.party_agent.multiplayer_id:

            agent = player_join.create_multiplayer_party_agent()
            self.client_agents[player_join.multiplayer_id] = agent
            self._update_multiplayer_npc_registration()
            self.log(f"Another player has joined this session: remote_multiplayer_id={player_join.multiplayer_id}")

    def _accept_player_leave(self, player_leave: PlayerLeave, network_id: str = None):
        agent = self.client_agents[player_leave.multiplayer_id]
        if agent is None:
            self.log(f"WARNING: Got leave notice for unknown multiplayer_id: {player_leave.multiplayer_id}")
        del self.client_agents[player_leave.multiplayer_id]            
        self.npc_service.remove_npc(agent)

        if self.server:
            assert network_id, "Must provide a network_id if called as a server/host"
            self.server.close_client(network_id)

    def _accept_location_update(self, location_update: LocationUpdate):

        if location_update.multiplayer_id != self.party_agent.multiplayer_id:

            agent = self.client_agents.get(location_update.multiplayer_id)
            if agent:
                location_update.update_agent(agent)
                self._update_multiplayer_npc_registration()
            else:
                self.log(f"WARNING: LocationUpdate for unknown multiplayer_id={location_update.multiplayer_id}")

    def _update_multiplayer_npc_registration(self):
        
        current_host_location = self.party_agent.get_current_location()

        # if a remote player is on the same location/level as you (the host) then add them to the NPC registry
        for _, agent in self.client_agents.items():
            same_location = agent.location_index == current_host_location.location_index
            same_level = agent.level_index == current_host_location.level_index
            if same_location and same_level:
                self.npc_service.add_npc(agent)
            else:
                self.npc_service.remove_npc(agent)


    # ===============================
    #
    #          PUBLIC API
    #
    # ===============================

    def read_updates(self):
        if self.server:
            self.read_client_updates()
        elif self.client:
            self.read_server_updates()           

    def write_updates(self):
        if self.server:
            self.write_client_updates()
        elif self.client:
            self.write_server_updates()           

    def pass_time(self, party_location):
        self.read_updates()
        self.write_updates()

    def quit(self):
        if self.server:
            self.server.write(ConnectTerminate())
            self.server.close()
            self.server = None
        elif self.client:
            self.client.write(PlayerLeave(self.party_agent.multiplayer_id))
            self.client.close()
            self.client = None

                
        
