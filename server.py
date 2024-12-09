import socket
import threading

HOST = '127.0.0.1'
PORT = 8000

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Server started on {HOST}:{PORT}")

# List to keep track of connected clients
clients = []

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except Exception as e:
                print(f"Error sending message to {client}: {e}")
                clients.remove(client)  # For disconnection
                print(f"Client {client} disconnected.")

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)  # Buffer size
            if not message:  # Check if message is empty
                print("Client disconnected.")
                break
            print(f"ServerReceived: {message.decode('utf-8')}")
            broadcast(message, client_socket)
        except Exception as e:
            print(f"Error handling client: {e}")
            break
    clients.remove(client_socket)
    client_socket.close()

def accept_clients():
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")

        # Add client to list
        clients.append(client_socket)

        # Start a new thread for the client
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    try:
        accept_clients()
    except KeyboardInterrupt:
        print("Server shutting down...")
        server_socket.close()
