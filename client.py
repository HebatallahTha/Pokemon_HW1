import socket
import sys
import select

SERVER_PORT = 2162
BUFFER_SIZE = 4096


def main():


    if len(sys.argv) != 2:
        print("Usage: python3 client.py SERVER_IP")
        return

    server_host = sys.argv[1]

    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_host, SERVER_PORT))
        print("Connected to the server!")
        print("Enter commands (LOGIN, BUY, SELL, LIST, etc.)")

    except OSError as error:
        print("Could not connect to server:", error)
        client_socket.close()
        return

    receive_buffer = ""

    running = True

    try:
        while running:

            readable, _, _ = select.select(
                [sys.stdin, client_socket], [], []
            )

            for source in readable:

            
                if source == client_socket:

                    data = client_socket.recv(BUFFER_SIZE)

                    
                    if not data:
                        print("\nServer disconnected.")
                        running = False
                        break

                    
                    receive_buffer += data.decode("utf-8", errors="replace")

            
                    while "\n" in receive_buffer:

                        message, receive_buffer = receive_buffer.split("\n", 1)

                        if message:
                            print("\nServer:", message)

                        
                        if message.startswith("210"):
                            print("Server is shutting down.")
                            running = False
                            break

                    if not running:
                        break

                
                elif source == sys.stdin:

                    command = sys.stdin.readline()

                    
                    if not command:
                        print("\nInput closed. Exiting...")
                        running = False
                        break

                    command = command.strip()

                    if not command:
                        continue

                    try:
                        client_socket.sendall(
                            (command + "\n").encode("utf-8")
                        )

                    except OSError as error:
                        print("Could not send command:", error)
                        running = False
                        break
                    
                    if command.upper() == "QUIT":
                        print("QUIT sent. Closing connection...")
                        running = False
                        break

    except KeyboardInterrupt:
        print("\nClient interrupted.")

    except OSError as error:
        print("Communication error:", error)

    finally:
        client_socket.close()
        print("Client closed.")


if __name__ == "__main__":
    main()
