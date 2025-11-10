import time
import traceback
from typing import Iterable, Protocol
from abc import ABC, abstractmethod

import queue
import threading

from dark_libraries.logging import LoggerMixin

PACKET_SIZE = 1024
QUEUE_SIZE = 10


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


class DarkNetworkTransport(Protocol):
    def send(self, data: bytes): ...
    def recv(self, buffer_size: int) -> bytes: ...

class DarkNetworkListener(Protocol):
    def listen(self): ...
    def accept(self) -> DarkNetworkTransport: ...
    def stop(self): ...
    def close(self): ...

class DarkNetworkProtocol[TMessage](Protocol):
    def encode(self, message: TMessage) -> bytes: ...
    def decode(self, data: bytes) -> list[TMessage]: ...

class DarkNetworkConnection(LoggerMixin):
    def __init__(
                    self, 
                    transport: DarkNetworkTransport, 
                    protocol: DarkNetworkProtocol, 
                    network_id: str, 
                    error_queue: queue.Queue
                 ):
        super().__init__()
        self.transport   = transport
        self.protocol    = protocol
        self.network_id  = network_id
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
            while self.is_alive:
                data = self.transport.recv(PACKET_SIZE)
                if not data:
                    continue
                for message in self.protocol.decode(data):
                    self.log(f"DEBUG: Received from {self.network_id}: {message}")
                    self.incoming.put(message)
                time.sleep(0) # yield thread

        except Exception as e:
            self.log(f"ERROR: Reader failed for {self.network_id}: {e}\n{traceback.format_exc()}")
            self.error_queue.put((self, e))
        finally:
            self.log("Reader thread finished.")
            self.incoming.shutdown(immediate=True)
                
    def writer(self):
        try:
            while self.is_alive:
                while not self.outgoing.empty():
                    try:
                        msg = self.outgoing.get(timeout=1.0)
                        self.log(f"DEBUG: Sending message to {self.network_id}: {msg}")
                        self.transport.send(self.protocol.encode(msg))
                    except queue.Empty:
                        pass
                time.sleep(0) # yield thread

            self.log(f"Flushing {self.outgoing.qsize()} remaining outgoing messages")

            while not self.outgoing.empty():
                msg = self.outgoing.get()
                self.log(f"DEBUG: Sending message to {self.network_id}: {msg}")
                self.transport.send(self.protocol.encode(msg))

            self.log(f"Outgoing queue empty, writer thread finished.")

        except Exception as e:
            self.log(f"ERROR: Writer failed for {self.network_id}: {e}\n{traceback.format_exc()}")
            self.error_queue.put((self, e))
        finally:
            self.log("DEBUG: writer thread finished.")
            self.outgoing.shutdown(immediate=True)

    def close(self):

        self.is_alive = False

        # 5. Join threads
        self.incoming_thread.join(timeout=5.0)
        self.outgoing_thread.join(timeout=5.0)


class DarkNetworkInterface[TMessage](ABC):

    @abstractmethod
    def read_all(self) -> Iterable[tuple[str, TMessage]]: ...

    @abstractmethod
    def write(self, message: TMessage): ...

    @abstractmethod
    def close(self): ...

class DarkNetworkServer[TMessage](LoggerMixin, DarkNetworkInterface[TMessage]):

    def launch(self):
        self.is_alive = True
        self.remote_clients = dict[str, DarkNetworkConnection]()

        self.error_queue = queue.Queue()

        self.server_thread_handle = threading.Thread(target=self.server_thread)
        self.server_thread_handle.start()

    def close(self):
        self.log("Shutting down")

        # Stop accepting new connections from clients.
        self.is_alive = False
        if self.server_thread_handle:
            self.log("DEBUG: Waiting for server listener thread to finish.")
            self.server_thread_handle.join()

        # Close down existing clients.
        self.log("DEBUG: Closing remote client connections.")
        for remote_client in self.remote_clients.values():
            remote_client.close()
        self.remote_clients.clear()
        self.log("DEBUG: Server has finished closing.")

    def close_client(self, network_id: str):
        client = self.remote_clients[network_id]
        client.close()
        del self.remote_clients[network_id]
        self.log(f"Closed and removed client connection: network_id={network_id}.  Remaining clients: {len(self.remote_clients)}")

    def read_all(self) -> Iterable[tuple[str, TMessage]]:
        messages = []
        for network_id, client in list(self.remote_clients.items()):
            while not client.incoming.empty():
                message = network_id, client.incoming.get()
                messages.append(message)
        return messages

    def write(self, message: TMessage):
        for network_id in list(self.remote_clients.keys()):
            self.write_to(network_id, message)

    def write_to(self, network_id: int, message: TMessage):
        client = self.remote_clients[network_id]
        assert client.is_alive, f"Cannot write to a dead client network_id={network_id}, message={message}"
        assert not client.outgoing.full(), f"Outgoing queue was allowed to fill up. network_id={network_id}"

        qsize = client.outgoing.qsize()
        if qsize > QUEUE_SIZE // 2:
            self.log(f"WARNING: Outgoing queue is filling up: network_id={network_id}, qsize={qsize}")

        client.outgoing.put(message)

    @abstractmethod
    def server_thread(self): ...

    def close_failed_connections(self):

        while not self.error_queue.empty():
            queue_entry: tuple[DarkNetworkConnection, Exception] = self.error_queue.get()
            connection, error = queue_entry
            self.log(f"Removing client {connection.network_id} due to error: {error}")
            connection.close()
            if connection in self.remote_clients:
                del self.remote_clients[connection.network_id]

class DarkNetworkClient[TMessage](DarkNetworkInterface[TMessage]):
    def __init__(self, connection: DarkNetworkConnection):
        self._connection = connection

    def read(self) -> TMessage:
        if self._connection.incoming.empty():
            return None
        else:
            return self._connection.incoming.get()

    def read_all(self) -> Iterable[TMessage]:
        messages = []
        while not self._connection.incoming.empty():
            messages.append(self._connection.incoming.get())
        return messages

    def write(self, message: TMessage):
        self._connection.outgoing.put(message)
