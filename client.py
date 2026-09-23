# client.py file here......

import socket
import sys

SERVER_PORT = 5432
MAX_LINE = 256

# Check that the server address was provided
if len(sys.argv) != 2:
    print("Usage: python client.py SERVER_HOST")
    sys.exit(1)

server_host = sys.argv[1]

# Create the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((server_host, SERVER_PORT))

# Keep sending messages to the server
while True:
    message = input("Enter a message: ")

    # Send the message to the server
    client_socket.send(message.encode())

    # Receive the server's response
    response = client_socket.recv(MAX_LINE).decode()

    print("Server:", response)

    # QUIT closes this client
    if message == "QUIT":
        break

    # SHUTDOWN closes this client and the server
    if message == "SHUTDOWN":
        break

# Close the client socket
client_socket.close()