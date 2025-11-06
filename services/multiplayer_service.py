from dark_libraries.dark_events import DarkEventListenerMixin
from dark_libraries.dark_math import Coord
from dark_libraries.dark_network import DarkUtf8SocketServer, DarkUtf8SocketClient
from dark_libraries.logging import LoggerMixin

from models.agents.multiplayer_party_agent import MultiplayerPartyAgent
from models.agents.party_agent import PartyAgent
from models.global_location import GlobalLocation

from services.info_panel_service import InfoPanelService
from services.npc_service import NpcService

DELIMITER = "|" #chr(0)

CONNECT_REQUEST = "connect_request"
CONNECT_ACCEPT  = "connect_accept"
LOCATION_UPDATE = "location_update"
PLAYER_JOIN     = "player_join"
PLAYER_LEFT     = "player_left"

def location_to_message_fragment(location: GlobalLocation):
    return [
        location.location_index,
        location.level_index,
        location.coord.x,
        location.coord.y
    ]

def to_message_gram(message_name: str, data: list[str]):
    return DELIMITER.join([message_name] + [str(x) for x in data])

def from_message_gram(message: str) -> tuple[str, tuple]:
    parts = message.split(DELIMITER)
    message_name = parts[0]
    data = tuple(parts[1:])
    return message_name, data

def location_update(agent: MultiplayerPartyAgent | PartyAgent):
    return to_message_gram(LOCATION_UPDATE, [agent.multiplayer_id] + location_to_message_fragment(agent.location))

class MultiplayerService(LoggerMixin, DarkEventListenerMixin):

    npc_service: NpcService
    party_agent: PartyAgent
    info_panel_service: InfoPanelService

    def __init__(self):
        super().__init__()
        self.server: DarkUtf8SocketServer = None
        self.client: DarkUtf8SocketClient = None
        self.client_agents = dict[str, MultiplayerPartyAgent]()

    # =====================================
    #
    #               SERVER
    #
    # =====================================

    def start_hosting(self):
        assert (not self.server) and (not self.client), f"Cannot start hosting: server={self.server}, self={self.client}"

        self.server = DarkUtf8SocketServer("127.0.0.1", 5000)
        self.server.launch()
        self.party_agent.set_multiplayer_id()
        self.party_agent.party_members[0]._character_record.name = "SERVER"
        self.info_panel_service.update_party_summary()

    def read_client_updates(self):

        for network_id, message_gram in self.server.read():
            try:
                message_name, message_data = from_message_gram(message_gram)

                if message_name == CONNECT_REQUEST:
                    self._connect_new_client(network_id, message_data)

                elif message_name == LOCATION_UPDATE:
                    self._accept_location_update(message_data)

            except Exception as e:
                self.log(f"ERROR: Could not parse message ({message_gram}) from client {network_id}: {e}")


    def write_client_updates(self):

        # Send your (the host)'s location to all remote players
        self.server.write(location_update(self.party_agent))

        # Send everyone's location to all remote players
        player_location_message_grams = [
            location_update(agent)
            for agent in self.client_agents.values()
        ]
        for message_gram in player_location_message_grams:
            self.server.write(message_gram)

    def _connect_new_client(self, network_id: str, message_data: tuple):

        name, dexterity, location_index, level_index, x, y = message_data

        location = GlobalLocation(
            int(location_index), 
            int(level_index), 
            Coord(int(x),int(y))
        )
        #
        # TODO: Check if there's another registered player at this location (overworld)
        #
        agent = MultiplayerPartyAgent(
            name, 
            int(dexterity),
            location
        )
        self.client_agents[agent.multiplayer_id] = agent
        self._update_multiplayer_npc_registration()

        # Update the new client with it's multiplayer_id and it's spawn location (might be different to requested spawn location)
        connect_accept_message_gram = to_message_gram(CONNECT_ACCEPT, [agent.multiplayer_id] + location_to_message_fragment(agent.location))
        self.server.write_to(network_id, connect_accept_message_gram)

        # Tell the new guy about all the other people in the lobby
        for other_agent in self.client_agents.values():
            player_join_message_data = [other_agent.name, other_agent.dexterity, other_agent.multiplayer_id] + location_to_message_fragment(other_agent.location)
            self.server.write(to_message_gram(PLAYER_JOIN, player_join_message_data))

        # Tell the new guy about ME
        player_join_message_data = [self.party_agent.name, self.party_agent.dexterity, self.party_agent.multiplayer_id] + location_to_message_fragment(self.party_agent.location)
        self.server.write(to_message_gram(PLAYER_JOIN, player_join_message_data))

        self.log(f"Player '{name}' has joined with network_id={network_id}, multiplayer_id={agent.multiplayer_id}")

    # ======================================================
    #
    #                       CLIENT
    #
    # ======================================================

    def connect_to_host(self, host: str, port: int):
        assert (not self.server) and (not self.client), f"Cannot connect to host: server={self.server}, client={self.client}"
        self.client = DarkUtf8SocketClient(host, port)

        current_client_location = self.party_agent.get_current_location()
        message_data = [self.party_agent.name, self.party_agent.dexterity] + location_to_message_fragment(current_client_location)
        message_gram = to_message_gram(CONNECT_REQUEST, message_data)
        self.client.write(message_gram)

    def read_server_updates(self):

        if self.party_agent._multiplayer_id is None:
            self._read_connect_accept()
            return

        for message_gram in self.client.read():
            message_name, message_data = from_message_gram(message_gram)
            
            if message_name == PLAYER_JOIN:
                self._accept_player_join(message_data)
                
            elif message_name == LOCATION_UPDATE:
                self._accept_location_update(message_data)

    def write_server_updates(self):

        message_gram = location_update(self.party_agent)
        self.client.write(message_gram)

    def _read_connect_accept(self):
        for message_gram in self.client.read():
            message_name, message_data = from_message_gram(message_gram)
            if message_name == CONNECT_ACCEPT:
                remote_multiplayer_id, _, _, x, y = message_data
                self.party_agent.set_multiplayer_id(remote_multiplayer_id)
                self.party_agent.change_coord(Coord(int(x),int(y)))
                self.log(f"Connnection to server accepted, remote_multiplayer_id={remote_multiplayer_id}")
                return
        self.log(f"WARNING: Have not received {CONNECT_ACCEPT}, so no remote_multiplayer_id is yet assigned.")

    # ===============================
    #
    # SHARED
    #
    # ===============================

    def _accept_player_join(self, message_data: tuple):

        name, dexterity, remote_multiplayer_id, location_index, level_index, x, y = message_data

        if remote_multiplayer_id != self.party_agent.multiplayer_id:

            location = GlobalLocation(
                int(location_index), 
                int(level_index), 
                Coord(int(x),int(y))
            )
            agent = MultiplayerPartyAgent(
                name, 
                dexterity,
                location,
                remote_multiplayer_id
            )
            self.client_agents[remote_multiplayer_id] = agent
            self._update_multiplayer_npc_registration()
            self.log(f"Another player has joined this session: remote_multiplayer_id={remote_multiplayer_id}")

    def _accept_location_update(self, message_data: tuple):

        remote_multiplayer_id, location_index, level_index, x, y = message_data

        if remote_multiplayer_id != self.party_agent.multiplayer_id:

            self.client_agents[remote_multiplayer_id].location = GlobalLocation(
                int(location_index), 
                int(level_index), 
                Coord(int(x),int(y))
            )
            self._update_multiplayer_npc_registration()


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
                
        
