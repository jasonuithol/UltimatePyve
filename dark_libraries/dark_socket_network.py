import ipaddress
import time
import queue
import socket
import traceback

from dark_libraries.dark_network import DarkNetworkClient, DarkNetworkConnection, DarkNetworkListener, DarkNetworkProtocol, DarkNetworkServer, DarkNetworkTransport
from dark_libraries.logging import LoggerMixin

# ===============================================================================================================================
#
# General Rule: 
# 
# If you create it, you close it. Don't delegate that responsibility to some other class, 
# otherwise everything ends up with a close method.
#
# "it" is either a thread or a socket.
#
# If a class creates one, it might need a close method.  Was it passed into the constructor instead ?  Then no.
#
# ===============================================================================================================================

# Whoever calls this has the job of closing the socket.
def _create_timingout_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Socket options
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.settimeout(1.0)
    return sock

def get_machine_address() -> str:
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    ip = ipaddress.ip_address(ip_address)
    if ip.is_loopback:
        print("(dark_socket_network) Falling back to DGRAM method for obtaining machine address")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to be reachable, just used to pick an interface
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        finally:
            s.close()
    return ip_address       

LISTENER_PORT = 5000

class DarkSocketTransport(DarkNetworkTransport):
    def __init__(self, socket_connection: socket.socket, address: tuple[str, int]):
        self.socket_connection = socket_connection
        self.address = address

    def send(self, data: bytes):
        self.socket_connection.sendall(data)

    def recv(self, buffer_size: int) -> bytes:
        try:
            return self.socket_connection.recv(buffer_size)
        except socket.timeout:
            return None

class DarkSocketListener(LoggerMixin, DarkNetworkListener):

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._is_alive = False
        LoggerMixin.__init__(self)

    def listen(self):

        self._sock = _create_timingout_socket()

        self._is_alive = True            
        self._sock.bind((self._host, self._port))
        self._sock.listen()
        self.log(f"Listening for incoming connections on {self._host}:{self._port}, timeout={self._sock.gettimeout()}")

    def accept(self) -> DarkSocketTransport:
        timeout = self._sock.gettimeout()
        assert timeout and timeout > 0, "Cannot block on accept"
        while self._is_alive:
            try:
                socket_connection, address = self._sock.accept()
                return DarkSocketTransport(socket_connection, address)
            except socket.timeout:
                return None
            finally:
                time.sleep(0.0)

        self.log("Listener has stopped accepting incoming connections.")

    def stop(self):
        self._is_alive = False

    def close(self):
        self._sock.close()
        self.log("Listener has closed")

class DarkSocketServer[TMessage](DarkNetworkServer[TMessage]):

    def __init__(self, protocol: DarkNetworkProtocol[TMessage]):
        LoggerMixin.__init__(self)
        self.host = get_machine_address()
        self.port = LISTENER_PORT
        self.protocol = protocol
        self.listener = DarkSocketListener(self.host, self.port) # I created the listener, I call close on the listener

    @property
    def network_id(self):
        return f"{self.host}:{self.port}"

    def server_thread(self):

        self.log(f"Starting listener on {self.host}:{self.port}")
        self.listener.listen()

        while self.is_alive:

            self.close_failed_connections()

            try:
                transport = self.listener.accept()
                if transport is None:
                    continue

                client_host, client_port = transport.address
                client_connection = DarkNetworkConnection(
                    transport   = transport, 
                    protocol    = self.protocol, 
                    network_id  = f"{client_host}:{client_port}", 
                    error_queue = self.error_queue
                )

                self.remote_clients[client_connection.network_id] = client_connection

                self.log(f"Spawned client handler for {transport.address}")

            except Exception as e:
                self.log(f"ERROR: Listener failure: {e}\n{traceback.format_exc()}")
                break

            time.sleep(0) # yield thread

        self.log(f"Server stopped listening on {self.host}:{self.port}")

    def close(self):
        self.listener.stop()
        super().close()
        self.listener.close() # Job done

class DarkSocketClient[TMessage](LoggerMixin, DarkNetworkClient[TMessage]):

    def __init__(self, host: str, port: int, protocol: DarkNetworkProtocol[TMessage]):

        # Create socket and connect to server
        self._sock = _create_timingout_socket() # Created it, have to close it
        self._sock.connect((host, port))

        # Wrap in transport
        transport = DarkSocketTransport(self._sock, (host, port))
        self.error_queue = queue.Queue()

        # Create the underlying connection (now it's my job to close that connection later)
        conn = DarkNetworkConnection(
            transport=transport,
            protocol=protocol,
            network_id=f"{host}:{port}",
            error_queue=self.error_queue
        )

        # assigns to self._connection
        super().__init__(connection = conn)

    def close(self):
        super().close() # TODO: does nothing ?
        self._connection.close() # Job done
        self._sock.close() # Job done
        self.log("Client has closed")


