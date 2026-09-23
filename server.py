import socket

SERVER_PORT = 5432
MAX_PENDING = 5
MAX_LINE = 256

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("", SERVER_PORT))

server_socket.listen(MAX_PENDING)

print("Server is waiting for a connection...")

while True:
    client_socket, client_address = server_socket.accept()

    print("Client connected.")
    
    while True:
        message = client_socket.recv(MAX_LINE).decode()
        if not message:
            break
        print("Received from client:", message)
        response = "Message received: " + message
        client_socket.send(response.encode())
    
    client_socket.close()