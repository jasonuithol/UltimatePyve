import threading
import time
import traceback

from typing import Callable, NamedTuple

import pygame

from dark_libraries.dark_events import DarkEventListenerMixin, DarkEventService
from dark_libraries.dark_socket_network import DarkSocketClient, DarkSocketServer
from dark_libraries.dark_tuple_network_protocol import DarkNamedTupleProtocol
from dark_libraries.logging import LoggerMixin

from models.agents.monster_agent import MonsterAgent
from models.agents.npc_agent import NpcAgent
import models.multiplayer_protocol
from models.agents.multiplayer_party_agent import MultiplayerPartyAgent
from models.agents.party_agent import PartyAgent
from models.multiplayer_protocol import ConnectAccept, ConnectRequest, ConnectTerminate, LocationUpdate, PlayerJoin, PlayerLeave

from services.console_service import ConsoleService
from services.info_panel_service import InfoPanelService
from services.multiplayer_message_factory import MultiplayerMessageFactory
from services.npc_service import NpcService

# If you're changing one of these, you may need to change the other
ProtocolFormat     = NamedTuple
ProtocolDefinition = models.multiplayer_protocol

ACTION_POINTS_PER_SECOND: float = 2.5
TURN_LENGTH: float = 1.0

class MultiplayerService(LoggerMixin, DarkEventListenerMixin):

    npc_service: NpcService
    party_agent: PartyAgent
    info_panel_service: InfoPanelService
    multiplayer_message_factory: MultiplayerMessageFactory
    dark_event_service: DarkEventService
    console_service: ConsoleService

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
        self.old_agent_name = self.party_agent.name
        self.party_agent.party_members[0]._character_record.name = "SERVER"
        self.info_panel_service.update_party_summary()

        self.start_reader_thread()

        #
        # Real-time action points
        #
        self.realtime_action_point_timer_thread_is_alive = True
        self.realtime_action_point_timer_thread = threading.Thread(
            target = self.realtime_action_point_thread_runner, 
            daemon = True
        )

        self.realtime_action_point_timer_thread.start()

    def monster_spawned(self, monster_agent: MonsterAgent):
        if self.server:
            player_join_message = self.multiplayer_message_factory.player_join(monster_agent)
            self.server.write(player_join_message)

    # NOTE: This runs in it's own thread
    def realtime_action_point_thread_runner(self):
        self.log("realtime_action_point_thread_runner started")

        ticks_at_launch = pygame.time.get_ticks()
        ticks_until_next_turn = ticks_at_launch + int(TURN_LENGTH * 1000)
        action_points_at_launch = self.party_agent.spent_action_points

        try:
            while self.realtime_action_point_timer_thread_is_alive:

                current_ticks = pygame.time.get_ticks()

                action_point_delta = ((current_ticks - ticks_at_launch) / 1000) * ACTION_POINTS_PER_SECOND
                realtime_action_points = action_points_at_launch + action_point_delta

                self.party_agent.spent_action_points = realtime_action_points

                for client_agent in self.client_agents.values():
                    client_agent.spent_action_points = realtime_action_points

                if ticks_until_next_turn < current_ticks:
                    ticks_until_next_turn = current_ticks + int(TURN_LENGTH * 1000)

                    self.console_service.print_ascii("tick")
                    self.dark_event_service.pass_time(self.party_agent.location)

                time.sleep(0.1)

        except Exception as e:
            self.log(f"ERROR: realtime_action_point_thread_runner encountered error: {e.with_traceback()}")

        self.log("realtime_action_point_thread_runner finished")

    def read_client_updates(self):

        for network_id, named_tuple in self.server.read_all():
            try:
                if isinstance(named_tuple, ConnectRequest):
                    self._connect_new_client(network_id, named_tuple)

                elif isinstance(named_tuple, LocationUpdate):
                    self._accept_location_update(named_tuple)

                elif isinstance(named_tuple, PlayerLeave):
                    self._accept_player_leave(named_tuple, network_id)

            except Exception as e:
                error_traceback = "\n".join(traceback.format_exception(e))
                self.log(f"ERROR: Error whilst processing message ({named_tuple}) from client {network_id}: {error_traceback}")

    def write_client_updates(self):

        location_update: Callable[[NpcAgent], LocationUpdate] = self.multiplayer_message_factory.location_update

        # Send your (the host)'s location to all remote players
        self.server.write(location_update(self.party_agent))

        # Send everyone's location to all remote players
        player_location_message_grams = [
            location_update(agent)
            for agent in self.client_agents.values()
        ]
        for message_gram in player_location_message_grams:
            self.server.write(message_gram)

        # Tell the new guy about the monsters
        for monster_agent in self.npc_service.get_monsters():
            self.server.write(location_update(monster_agent))

    def _connect_new_client(self, network_id: str, connect_request: ConnectRequest):

        #
        # TODO: Check if there's another registered player at this location (overworld)
        #
        agent = self.multiplayer_message_factory.create_multiplayer_party_agent(connect_request)

        self.client_agents[agent.multiplayer_id] = agent
        self._update_multiplayer_npc_registration()

        # Update the new client with it's multiplayer_id and it's spawn location (might be different to requested spawn location)
        connect_accept_message = self.multiplayer_message_factory.connect_accept(agent)
        self.server.write_to(network_id, connect_accept_message)

        # Update new client with all the existing npcs
        player_join: Callable[[NpcAgent], PlayerJoin] = self.multiplayer_message_factory.player_join

        # Tell the new guy about all the other people in the lobby
        for other_agent in self.client_agents.values():
            self.server.write(player_join(other_agent))

        # Tell the new guy about ME
        self.server.write(player_join(self.party_agent))

        # Tell the new guy about the monsters
        for monster_agent in self.npc_service.get_monsters():
            self.server.write(player_join(monster_agent))

        self.log(f"Player '{agent.name}' has joined with network_id={network_id}, multiplayer_id={agent.multiplayer_id}")


    # ======================================================
    #
    #                       CLIENT
    #
    # ======================================================

    def connect_to_host(self, host: str, port: int):

        assert (not self.server) and (not self.client), f"Cannot connect to host: server={self.server}, client={self.client}"

        self.client: DarkSocketClient[ProtocolFormat] = DarkSocketClient[ProtocolFormat](host, port, self.protocol)

        connect_request_message = self.multiplayer_message_factory.connect_request()
        self.client.write(connect_request_message)

        self.npc_service.join_server()

        self.start_reader_thread()

    def read_server_updates(self):

        if self.party_agent._multiplayer_id is None:
            self._read_connect_accept()
            return

        for named_tuple in self.client.read_all():
            
            if isinstance(named_tuple, PlayerJoin):
                self._accept_player_join(named_tuple)
                
            elif isinstance(named_tuple, PlayerLeave):
                self._accept_player_leave(named_tuple)

            elif isinstance(named_tuple, LocationUpdate):
                self._accept_location_update(named_tuple)

            elif isinstance(named_tuple, ConnectTerminate):
                self._accept_connect_terminate()

    def write_server_updates(self):

        location_update_message = self.multiplayer_message_factory.location_update(self.party_agent)
        self.client.write(location_update_message)

    def _read_connect_accept(self):
        named_tuple = self.client.read()
        if isinstance(named_tuple, ConnectAccept):
            self.multiplayer_message_factory.update_agent(self.party_agent, named_tuple)
            self.log(f"Connnection to server accepted, multiplayer_id={named_tuple.multiplayer_id}")
        else:
            self.log(f"ERROR: Dropping unexpected message: {named_tuple}")

        self.log(f"WARNING: Have not received ConnectAccept, so no multiplayer_id is yet assigned.")

    def _accept_connect_terminate(self):
        self.log(f"Server terminating connection, removing remote players and closing client connection.")
        self.quit()

    # ===============================
    #
    # SHARED
    #
    # ===============================

    def _accept_player_join(self, player_join: PlayerJoin):

        if player_join.multiplayer_id != self.party_agent.multiplayer_id:

            agent = self.multiplayer_message_factory.create_multiplayer_party_agent(player_join)
            self.client_agents[player_join.multiplayer_id] = agent
            self._update_multiplayer_npc_registration()
            self.log(f"Another player has joined this session: remote_multiplayer_id={player_join.multiplayer_id}")

    def _accept_player_leave(self, player_leave: PlayerLeave, network_id: str = None):

        agent = self.client_agents.get(player_leave.multiplayer_id, None)
        if agent is None:
            self.log(f"ERROR: Got leave notice for unknown multiplayer_id: {player_leave.multiplayer_id}")
            return
        
        del self.client_agents[player_leave.multiplayer_id]            
        self.npc_service.remove_npc(agent)

        if self.server:
            assert network_id, "Must provide a network_id if called as a server/host"
            self.server.close_client(network_id)

    def _accept_location_update(self, location_update: LocationUpdate):

        if location_update.multiplayer_id != self.party_agent.multiplayer_id:

            agent = self.client_agents.get(location_update.multiplayer_id)
            if agent:
                self.multiplayer_message_factory.update_agent(agent, location_update)
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

    # DarkEventListenerMixin: Start
    #
    def pass_time(self, party_location):
        self.read_updates()
        self.write_updates()

    def quit(self):

        if self.server:
            self.server.write(ConnectTerminate())
            self.server.close()
            self.server = None
            self.client_agents.clear()
            self.party_agent.clear_multiplayer_id()

            self.party_agent.party_members[0]._character_record.name = self.old_agent_name
            self.info_panel_service.update_party_summary()

            self.stop_reader_thread()

            self.realtime_action_point_timer_thread_is_alive = False
            self.realtime_action_point_timer_thread.join()

        elif self.client:
            self.client.write(PlayerLeave(self.party_agent.multiplayer_id))
            self.client.close()
            self.client = None
            self.client_agents.clear()
            self.npc_service.leave_server()
            self.party_agent.clear_multiplayer_id()

            self.stop_reader_thread()

            self.party_agent.unfreeze_action_points()
    #
    # DarkEventListenerMixin: End

    #
    # update reader thread
    #

    def start_reader_thread(self):
        assert self._reader_thread_is_alive != True, "reader_thread already running"
        self._reader_thread_is_alive = True
        self._reader_thread_handle = threading.Thread(
            target = self.reader_thread_runner,
            daemon = True
        )
        self._reader_thread_handle.start()

    def stop_reader_thread(self):
        self._reader_thread_is_alive = False
        self._reader_thread_handle.join()

    def reader_thread_runner(self):
        while self._reader_thread_is_alive:
            self.read_updates()
            time.sleep(0.1)