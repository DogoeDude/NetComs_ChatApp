import socket
import threading
from datetime import datetime
import os

HOST = '127.0.0.1'
PORT = 8000

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Server started on {HOST}:{PORT}")

# Dictionary to keep track of connected clients and their usernames
clients = {}

def log_message(message):
    # Get current date for log file name
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = f'logs/chat_log_{current_date}.txt'
    
    # Add timestamp to message
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    
    # Write to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def broadcast(message, sender_socket):
    # Log the message
    decoded_message = message.decode('utf-8')
    log_message(decoded_message)
    
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                client_socket.send(message)
            except Exception as e:
                print(f"Error sending message to {clients[client_socket]}: {e}")
                remove_client(client_socket)

def remove_client(client_socket):
    if client_socket in clients:
        username = clients[client_socket]
        del clients[client_socket]
        client_socket.close()
        leave_message = f"System: {username} left the chat."
        broadcast(leave_message.encode('utf-8'), None)
        print(f"Client {username} disconnected.")

def handle_client(client_socket):
    # Wait for username
    try:
        message = client_socket.recv(1024).decode('utf-8')
        if message.startswith("USERNAME:"):
            username = message[9:]
            clients[client_socket] = username
            print(f"{username} joined the chat")
            join_message = f"System: {username} joined the chat."
            broadcast(join_message.encode('utf-8'), client_socket)
            
            while True:
                try:
                    message = client_socket.recv(1024)
                    if not message:
                        break
                    print(f"Received: {message.decode('utf-8')}")
                    broadcast(message, client_socket)
                except Exception as e:
                    print(f"Error handling client {username}: {e}")
                    break
    except Exception as e:
        print(f"Error setting username: {e}")
    
    remove_client(client_socket)

def accept_clients():
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")

        # Start a new thread for the client
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    try:
        accept_clients()
    except KeyboardInterrupt:
        print("Server shutting down...")
        for client_socket in clients:
            client_socket.close()
        server_socket.close()
