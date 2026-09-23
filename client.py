import socket
import sys

SERVER_PORT = 5432
MAX_LINE = 256

if len(sys.argv) != 2:
    print("Usage: python client.py SERVER_HOST")
    sys.exit(1)

server_host = sys.argv[1]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((server_host, SERVER_PORT))

while True:
    message = input("Enter a message: ")

    if message == "QUIT":
        break

    client_socket.send(message.encode())

    response = client_socket.recv(MAX_LINE).decode()

    print("Server:", response)

client_socket.close()