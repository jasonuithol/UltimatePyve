import threading
import socket
import queue

from dark_libraries.logging import LoggerMixin

PACKET_SIZE = 1024
QUEUE_SIZE = 10
ACK = b"ACK"

class DarkNetworkServer(LoggerMixin):
    def launch(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.stop_event = threading.Event()
        self.clients: list[DarkNetworkClient] = []

        self.server_thread_handle = threading.Thread(target=self.server_thread)
        self.server_thread_handle.start()

    def shutdown(self):
        self.stop_event.set()
        if self.server_thread_handle:
            self.server_thread_handle.join()

    def server_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            s.settimeout(1.0)

            self.log(f"Listening on {self.host}:{self.port}")
            while not self.stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    client = DarkNetworkClient(conn, addr, self.stop_event)
                    self.clients.append(client)
                    self.log(f"Spawned client handler for {addr}")
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log(f"ERROR: Listener failure: {e}")
                    break

        self.log(f"Shutting down listener: {self.host}:{self.port}")

class DarkNetworkClient(LoggerMixin):
    def __init__(self, connection: socket.socket, address: tuple[str, int], stop_event: threading.Event):
        self.connection = connection
        self.address = address
        self.incoming = queue.Queue(QUEUE_SIZE)
        self.outgoing = queue.Queue(QUEUE_SIZE)
        self.stop_event = stop_event

        threading.Thread(target=self.reader, daemon=True).start()
        threading.Thread(target=self.writer, daemon=True).start()

    def reader(self):
        with self.connection:
            try:
                while not self.stop_event.is_set():
                    data = self.connection.recv(PACKET_SIZE)
                    if not data:
                        break
                    message = data.decode(errors="replace")
                    self.log(f"DEBUG: Received from {self.address}: {message}")
                    self.incoming.put(message)
                    self.connection.sendall(ACK)
            except Exception as e:
                self.log(f"ERROR: Reader failed for {self.address}: {e}")

    def writer(self):
        try:
            while not self.stop_event.is_set():
                msg = self.outgoing.get()  # blocks until something to send
                self.connection.sendall(msg.encode())
        except Exception as e:
            self.log(f"ERROR: Writer failed for {self.address}: {e}")


'''
for client in server.clients:
    while not client.incoming.empty():
        event = client.incoming.get()
        apply_event(event, client)

    # push updates
    for update in world_updates:
        client.outgoing.put(update)
'''