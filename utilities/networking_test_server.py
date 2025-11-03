import threading
import socket

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    with conn:
        while data := conn.recv(1024):
            print(f"Received: {data.decode()}")
            conn.sendall(b"ACK")

def server_thread(host="127.0.0.1", port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# Launch the server in a background thread
threading.Thread(target=server_thread, daemon=True).start()

# Main thread can keep doing other work
while True:
    cmd = input("Main thread prompt> ")
    if cmd == "quit":
        break