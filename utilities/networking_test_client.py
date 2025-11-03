import socket
s = socket.create_connection(("127.0.0.1", 5000))
s.sendall(b"hello\n")
print(s.recv(1024))
s.close()
