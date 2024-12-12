import socket
import threading
from protocol import (
    MessageType, create_message, parse_message, format_message_for_display,
    create_handshake_message, setup_logging, ConnectionStatus, log_connection_status,
    log_error
)

#Initialize the client
HOST = '127.0.0.1'
PORT = 8000

# Get username when starting
username = input("Enter your username: ")

def receive_message():
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                msg_data = parse_message(message)
                print(format_message_for_display(msg_data))
            else:
                print("Disconnected from server.")
                break
        except Exception as e:
            print(f"Error occurred: {e}")
            client_socket.close()
            break

def send_message():
    while True:
        message = input("")
        if message.lower() == "/exit":
            client_socket.close()
            print("Disconnected from the server.")
            break
        chat_message = create_message(MessageType.CHAT, username, message)
        client_socket.send(chat_message)

def connect_to_server():
    try:
        client_socket.connect((HOST, PORT))
        log_connection_status(ConnectionStatus.CONNECTING)
        
        # Step 1: Send HELLO
        log_connection_status(ConnectionStatus.HANDSHAKE_STARTED)
        hello_msg = create_handshake_message(MessageType.HELLO)
        client_socket.send(hello_msg)
        
        # Step 2: Wait for HELLO_ACK
        response = parse_message(client_socket.recv(1024))
        if response["type"] != MessageType.HELLO_ACK.value:
            log_error("handshake", "Unexpected response from server")
            return False
            
        # Step 3: Send Username
        username_msg = create_message(MessageType.USERNAME, username, username)
        client_socket.send(username_msg)
        
        # Step 4: Wait for USERNAME_ACK
        response = parse_message(client_socket.recv(1024))
        if response["type"] != MessageType.USERNAME_ACK.value:
            log_error("username", "Username not accepted")
            return False
            
        log_connection_status(ConnectionStatus.CONNECTED)
        return True
        
    except Exception as e:
        log_error("connection", str(e))
        return False

# Replace the current connection code with:
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if not connect_to_server():
    exit()

# Send join message (after successful handshake)
join_message = create_message(MessageType.JOIN, username, "joined the chat")
client_socket.send(join_message)

# Start threads
receive_thread = threading.Thread(target=receive_message)
receive_thread.start()

send_thread = threading.Thread(target=send_message)
send_thread.start()
