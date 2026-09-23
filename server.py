
# server.py file here......

import socket
import db

SERVER_PORT = 5432
MAX_PENDING = 5
MAX_LINE = 256

# Create the database if it does not already exist
db.init_db()

# Create the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the server to port 5432
server_socket.bind(("", SERVER_PORT))

# Wait for client connections
server_socket.listen(MAX_PENDING)

print("Server is waiting for a connection...")

shutdown = False

# Keep accepting clients
while True:
    client_socket, client_address = server_socket.accept()

    print("Client connected.")

    # Handle messages from the current client
    while True:
        message = client_socket.recv(MAX_LINE).decode()

        if not message:
            break

        # Print every message received from the client
        print("Received from client:", message)

        parts = message.split()

        # Check for an empty command
        if len(parts) == 0:
            response = "Error: Empty command."

        # QUIT closes the current client connection
        elif parts[0] == "QUIT":
            response = "200 OK"
            client_socket.send(response.encode())
            break

        # SHUTDOWN stops the server
        elif parts[0] == "SHUTDOWN":
            response = "200 OK"
            client_socket.send(response.encode())
            shutdown = True
            break

        # LIST shows the user's cards
        elif parts[0] == "LIST":
            if len(parts) < 2:
                response = "Error: LIST requires a user ID."
            else:
                owner_id = parts[1]
                result = db.handle_list(owner_id)
                response = result["message"]

        # BALANCE shows the user's balance
        elif parts[0] == "BALANCE":
            if len(parts) < 2:
                response = "Error: BALANCE requires a user ID."
            else:
                owner_id = parts[1]
                result = db.handle_balance(owner_id)
                response = result["message"]

        # BUY adds cards and subtracts money
        elif parts[0] == "BUY":
            if len(parts) < 7:
                response = "Error: BUY requires 6 arguments."
            else:
                card_name = parts[1]
                card_type = parts[2]
                rarity = parts[3]
                price = parts[4]
                count = parts[5]
                owner_id = parts[6]

                result = db.handle_buy(
                    card_name,
                    card_type,
                    rarity,
                    price,
                    count,
                    owner_id
                )
                response = result["message"]

        # SELL removes cards and adds money
        elif parts[0] == "SELL":
            if len(parts) < 5:
                response = "Error: SELL requires 4 arguments."
            else:
                card_name = parts[1]
                count = parts[2]
                price = parts[3]
                owner_id = parts[4]

                result = db.handle_sell(
                    card_name,
                    count,
                    price,
                    owner_id
                )
                response = result["message"]

        # Handle unknown commands
        else:
            response = "Invalid command."

        # Send the response back to the client
        client_socket.send(response.encode())

    # Close the current client connection
    client_socket.close()

    # Stop the server if SHUTDOWN was requested
    if shutdown:
        break

# Close the server socket
server_socket.close()

print("Server shut down.")