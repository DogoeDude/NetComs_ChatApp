import socket
import threading
from datetime import datetime
import os
from protocol import (
    MessageType, create_message, parse_message, create_handshake_message,
    setup_logging, ConnectionStatus, log_connection_status, log_error
)
import multiprocessing
from multiprocessing import Pool, Process, Manager
from concurrent.futures import ThreadPoolExecutor
import queue
import json

HOST = '127.0.0.1'
PORT = 8000#anby ports below 1024 are for system services

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

class ChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        
        # Shared resources using multiprocessing Manager
        self.manager = Manager()
        self.clients = self.manager.dict()
        self.message_queue = self.manager.Queue()
        
        # Thread pool for client handling
        self.num_cores = multiprocessing.cpu_count()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.num_cores * 2)
        
        print(f"Server started on {HOST}:{PORT} with {self.num_cores} cores")

    def log_message(self, message):
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file = f'logs/chat_log_{current_date}.txt'
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def process_message(self, message_data):
        """Process message in a separate thread"""
        try:
            msg_data = parse_message(message_data)
            return msg_data
        except Exception as e:
            log_error("message_processing", str(e))
            return None

    def broadcast_message(self, message, sender_socket=None):
        """Broadcast message to all clients except sender"""
        try:
            msg_data = self.process_message(message)
            if msg_data:
                self.log_message(f"{msg_data['username']}: {msg_data['content']}")
                
                # Create broadcast tasks
                broadcast_tasks = []
                for client_socket in self.clients:
                    if client_socket != sender_socket:
                        broadcast_tasks.append((client_socket, message))
                
                # Submit broadcast tasks to thread pool
                futures = []
                for client_socket, msg in broadcast_tasks:
                    future = self.thread_pool.submit(self._send_to_client, client_socket, msg)
                    futures.append(future)
                
                # Wait for all broadcasts to complete
                for future in futures:
                    future.result()
                    
        except Exception as e:
            log_error("broadcast", str(e))

    def _send_to_client(self, client_socket, message):
        """Send message to a single client"""
        try:
            client_socket.send(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """Remove client from the system"""
        if client_socket in self.clients:
            username = self.clients[client_socket]
            del self.clients[client_socket]
            client_socket.close()
            leave_message = create_message(MessageType.SYSTEM, "System", f"{username} left the chat")
            self.broadcast_message(leave_message, None)
            print(f"Client {username} disconnected.")

    def handle_client(self, client_socket):
        """Handle client connection with parallel processing"""
        try:
            client_address = client_socket.getpeername()
            log_connection_status(ConnectionStatus.CONNECTING, f"from {client_address}")
            
            # Handshake process
            message = client_socket.recv(1024)
            msg_data = self.process_message(message)
            
            if msg_data["type"] != MessageType.HELLO.value:
                log_error("handshake", f"Client {client_address} didn't say HELLO")
                client_socket.close()
                return
                
            log_connection_status(ConnectionStatus.HANDSHAKE_STARTED, f"with {client_address}")
            
            # Send HELLO_ACK
            hello_ack = create_handshake_message(MessageType.HELLO_ACK)
            client_socket.send(hello_ack)
            
            # Get username
            message = client_socket.recv(1024)
            msg_data = self.process_message(message)
            
            if msg_data["type"] != MessageType.USERNAME.value:
                print("Expected username, got something else")
                client_socket.close()
                return
                
            username = msg_data["content"]
            self.clients[client_socket] = username
            username_ack = create_handshake_message(MessageType.USERNAME_ACK)
            client_socket.send(username_ack)
            
            log_connection_status(ConnectionStatus.CONNECTED, f"Client {username} fully connected")
            print(f"{username} joined the chat")
            
            # Message handling loop
            while True:
                try:
                    message = client_socket.recv(1024)
                    if not message:
                        break
                        
                    # Process message in parallel
                    msg_data = self.process_message(message)
                    if msg_data["type"] == MessageType.JOIN.value:
                        system_message = create_message(
                            MessageType.SYSTEM, 
                            "System", 
                            f"{username} joined the chat"
                        )
                        self.broadcast_message(system_message, client_socket)
                    else:
                        print(f"Received: {message.decode('utf-8')}")
                        self.broadcast_message(message, client_socket)
                        
                except Exception as e:
                    print(f"Error handling client {username}: {e}")
                    break
                    
        except Exception as e:
            log_error("client_handler", str(e))
        
        finally:
            if client_socket in self.clients:
                log_connection_status(
                    ConnectionStatus.DISCONNECTED, 
                    f"Client {self.clients[client_socket]} disconnected"
                )
            self.remove_client(client_socket)

    def accept_clients(self):
        """Accept and handle client connections"""
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                # Submit client handling to thread pool
                self.thread_pool.submit(self.handle_client, client_socket)
                
        except KeyboardInterrupt:
            print("Server shutting down...")
            # Cleanup
            self.thread_pool.shutdown()
            for client_socket in self.clients:
                client_socket.close()
            self.server_socket.close()

if __name__ == "__main__":
    setup_logging()
    server = ChatServer()
    server.accept_clients()
