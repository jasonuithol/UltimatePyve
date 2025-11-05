from typing import Iterable, Protocol
from abc import ABC, abstractmethod

import queue
import socket
import threading

from dark_libraries.logging import LoggerMixin

PACKET_SIZE = 1024
QUEUE_SIZE = 10

class DarkNetworkTransport(Protocol):
    def send(self, data: bytes): ...
    def recv(self, buffer_size: int) -> bytes: ...
    def close(self): ...

class DarkSocketTransport(DarkNetworkTransport):
    def __init__(self, socket_connection: socket.socket):
        self.socket_connection = socket_connection

    def send(self, data: bytes):
        self.socket_connection.sendall(data)

    def recv(self, buffer_size: int) -> bytes:
        return self.socket_connection.recv(buffer_size)

    def close(self):
        self.socket_connection.close()

class DarkNetworkProtocol[TMessage](Protocol):
    def encode(self, message: TMessage) -> bytes: ...
    def decode(self, data: bytes) -> list[TMessage]: ...

class DarkUtf8StringProtocol(DarkNetworkProtocol[str]):

    def __init__(self):
        self._buffer = b""

    def encode(self, message: str) -> bytes:
        return message.encode("utf-8") + b"\n"

    def decode(self, data: bytes) -> list[str]:
        self._buffer += data
        messages = []
        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            messages.append(line.decode("utf-8", errors="replace"))
        return messages

class DarkNetworkConnection(LoggerMixin):
    def __init__(
                    self, 
                    transport: DarkNetworkTransport, 
                    protocol: DarkNetworkProtocol, 
                    network_id: str, 
                    stop_event: threading.Event, 
                    error_queue: queue.Queue
                 ):
        super().__init__()
        self.transport   = transport
        self.protocol    = protocol
        self.network_id  = network_id
        self.stop_event  = stop_event
        self.error_queue = error_queue

        self.is_alive = True

        self.incoming = queue.Queue(QUEUE_SIZE)
        self.incoming_thread = threading.Thread(target=self.reader)
        self.incoming_thread.start()

        self.outgoing = queue.Queue(QUEUE_SIZE)
        self.outgoing_thread = threading.Thread(target=self.writer)
        self.outgoing_thread.start()

    def reader(self):
        try:
            while self.is_alive and (not self.stop_event.is_set()):
                data = self.transport.recv(PACKET_SIZE)
                if not data:
                    break
                for message in self.protocol.decode(data):
                    self.log(f"DEBUG: Received from {self.network_id}: {message}")
                    self.incoming.put(message)
        except Exception as e:
            self.log(f"ERROR: Reader failed for {self.network_id}: {e}")
            self.error_queue.put((self, e))
        finally:
            self.log("DEBUG: reader thread finished.")

    def writer(self):
        try:
            while self.is_alive and (not self.stop_event.is_set()):
                msg = self.outgoing.get()  # blocks until something to send
                self.transport.send(self.protocol.encode(msg))
        except Exception as e:
            self.log(f"ERROR: Writer failed for {self.network_id}: {e}")
            self.error_queue.put((self, e))
        finally:
            self.log("DEBUG: writer thread finished.")

    def close(self):
        self.is_alive = False
        self.transport.close()     
        self.incoming_thread.join()
        self.outgoing_thread.join()

class DarkNetworkInterface[TMessage](ABC):

    @abstractmethod
    def read(self) -> Iterable[tuple[str, TMessage]]: ...

    @abstractmethod
    def write(self, message: TMessage): ...

    @abstractmethod
    def close(self): ...

class DarkNetworkServer[TMessage](LoggerMixin, DarkNetworkInterface[TMessage]):

    def launch(self):
        self.stop_event = threading.Event()
        self.remote_clients = dict[str, DarkNetworkConnection]()

        self.server_thread_handle = threading.Thread(target=self.server_thread)
        self.server_thread_handle.start()

        self.error_queue = queue.Queue()

    def close(self):
        self.log("Shutting down")
        self.stop_event.set()
        if self.server_thread_handle:
            self.server_thread_handle.join()
        for remote_client in self.remote_clients.values():
            remote_client.close()
        self.remote_clients.clear()

    def read(self) -> Iterable[tuple[str, TMessage]]:
        for network_id, client in self.remote_clients.items():
            try:
                yield network_id, client.incoming.get_nowait()
            except queue.Empty:
                # skip exceptions from empty reads
                continue

    def write(self, message: TMessage):
        for client in self.remote_clients.values():
            client.outgoing.put(message)

    def write_to(self, network_id: int, message: TMessage):
        client = self.remote_clients[network_id]
        client.outgoing.put(message)

    @abstractmethod
    def server_thread(self): ...

    def _close_failed_connections(self):
        while not self.error_queue.empty():
            queue_entry: tuple[DarkNetworkConnection, Exception] = self.error_queue.get()
            connection, error = queue_entry
            self.log(f"Removing client {connection.network_id} due to error: {error}")
            connection.close()
            if connection in self.remote_clients:
                self.remote_clients.remove(connection)

class DarkUtf8SocketServer(DarkNetworkServer[str]):

    def __init__(self, host: str, port: int):
        LoggerMixin.__init__(self)
        self.host = host
        self.port = port
        self.protocol = DarkUtf8StringProtocol()

    @property
    def network_id(self):
        return f"{self.host}:{self.port}"

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.bind((self.host, self.port))
            s.listen()
            s.settimeout(1.0)

            self.log(f"Listening on {self.host}:{self.port}")
            while not self.stop_event.is_set():

                self._close_failed_connections()

                try:
                    socket_connection, address = s.accept()
                    client_host, client_port = address
                    #
                    # Create the Client
                    #
                    transport = DarkSocketTransport(socket_connection)
                    client_connection = DarkNetworkConnection(transport, self.protocol, f"{client_host}:{client_port}", self.stop_event, self.error_queue)

                    self.remote_clients[client_connection.network_id] = client_connection
                    self.log(f"Spawned client handler for {address}")
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log(f"ERROR: Listener failure: {e}")
                    break

        self.log(f"Shutting down listener: {self.host}:{self.port}")

class DarkNetworkClient[TMessage](DarkNetworkInterface[TMessage]):
    def __init__(self, connection: DarkNetworkConnection):
        self._connection = connection

    def read(self) -> Iterable[TMessage]:
        while not self._connection.incoming.empty():
            yield self._connection.incoming.get()

    def write(self, message: TMessage):
        self._connection.outgoing.put(message)

    def close(self):
        self._connection.close()

class DarkUtf8SocketClient(DarkNetworkClient[str]):

    def __init__(self, host: str, port: int):

        # Create socket and connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.connect((host, port))

        # Wrap in transport
        transport = DarkSocketTransport(sock)
        protocol = DarkUtf8StringProtocol()

        # Each client has its own stop_event
        self.stop_event = threading.Event()
        self.error_queue = queue.Queue()

        # Create the underlying connection
        connection = DarkNetworkConnection(
            transport=transport,
            protocol=protocol,
            network_id=f"{host}:{port}",
            stop_event=self.stop_event,
            error_queue=self.error_queue
        )

        super().__init__(connection)


'''
for incoming_message in server.read():
    apply_event(incoming_message)

for update in world_updates:
    server.write(update)
'''