import socket
import threading
from datetime import datetime
import os
from protocol import (
    MessageType, create_message, parse_message, create_handshake_message,
    setup_logging, ConnectionStatus, log_connection_status, log_error
)

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
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = f'logs/chat_log_{current_date}.txt'
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def broadcast(message, sender_socket):
    msg_data = parse_message(message)
    log_message(f"{msg_data['username']}: {msg_data['content']}")
    
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
        leave_message = create_message(MessageType.SYSTEM, "System", f"{username} left the chat")
        broadcast(leave_message, None)
        print(f"Client {username} disconnected.")

def handle_client(client_socket):
    try:
        client_address = client_socket.getpeername()
        log_connection_status(ConnectionStatus.CONNECTING, f"from {client_address}")
        
        # Step 1: Wait for HELLO
        message = client_socket.recv(1024)
        msg_data = parse_message(message)
        
        if msg_data["type"] != MessageType.HELLO.value:
            log_error("handshake", f"Client {client_address} didn't say HELLO")
            client_socket.close()
            return
            
        log_connection_status(ConnectionStatus.HANDSHAKE_STARTED, f"with {client_address}")
        
        # Step 2: Send HELLO_ACK
        hello_ack = create_handshake_message(MessageType.HELLO_ACK)
        client_socket.send(hello_ack)
        
        # Step 3: Wait for Username
        message = client_socket.recv(1024)
        msg_data = parse_message(message)
        
        if msg_data["type"] != MessageType.USERNAME.value:
            print("Expected username, got something else")
            client_socket.close()
            return
            
        # Step 4: Accept Username and send acknowledgment
        username = msg_data["content"]
        clients[client_socket] = username
        username_ack = create_handshake_message(MessageType.USERNAME_ACK)
        client_socket.send(username_ack)
        
        print(f"{username} joined the chat")
        
        # Now wait for normal chat messages
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                msg_data = parse_message(message)
                if msg_data["type"] == MessageType.JOIN.value:
                    system_message = create_message(
                        MessageType.SYSTEM, 
                        "System", 
                        f"{username} joined the chat"
                    )
                    broadcast(system_message, client_socket)
                else:
                    print(f"Received: {message.decode('utf-8')}")
                    broadcast(message, client_socket)
            except Exception as e:
                print(f"Error handling client {username}: {e}")
                break
                
        log_connection_status(ConnectionStatus.CONNECTED, f"Client {username} fully connected")
        
    except Exception as e:
        log_error("client_handler", str(e))
    
    finally:
        if client_socket in clients:
            log_connection_status(
                ConnectionStatus.DISCONNECTED, 
                f"Client {clients[client_socket]} disconnected"
            )
        remove_client(client_socket)

def accept_clients():
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")
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
