import json
from enum import Enum
from datetime import datetime
import logging
import os

# Set up logging
def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set up logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            # File handler for debug logs
            logging.FileHandler(f'logs/debug_{datetime.now().strftime("%Y-%m-%d")}.log'),
            # Console handler
            logging.StreamHandler()
        ]
    )

# Connection status codes
class ConnectionStatus(Enum):
    CONNECTING = "Initiating connection"
    HANDSHAKE_STARTED = "Starting handshake"
    HANDSHAKE_COMPLETE = "Handshake complete"
    USERNAME_ACCEPTED = "Username accepted"
    CONNECTED = "Fully connected"
    DISCONNECTED = "Disconnected"
    ERROR = "Connection error"

def log_connection_status(status: ConnectionStatus, details: str = None):
    """Log connection status with optional details"""
    message = f"Connection Status: {status.value}"
    if details:
        message += f" - {details}"
    if status == ConnectionStatus.ERROR:
        logging.error(message)
    else:
        logging.info(message)

class MessageType(Enum):
    HELLO = "hello"
    HELLO_ACK = "hello_ack"
    USERNAME = "username"
    USERNAME_ACK = "username_accepted"
    JOIN = "join"
    CHAT = "chat"
    LEAVE = "leave"
    SYSTEM = "system"
    ERROR = "error"  # Add error type

def create_message(msg_type: MessageType, username: str, content: str, timestamp: str = None) -> bytes:
    """Create a formatted message following the chat protocol"""
    if timestamp is None:
        timestamp = datetime.now().strftime('%H:%M:%S')
        
    return json.dumps({
        "type": msg_type.value,
        "username": username,
        "content": content,
        "timestamp": timestamp
    }).encode('utf-8')

def parse_message(message: bytes) -> dict:
    """Parse a received message from bytes to dictionary"""
    return json.loads(message.decode('utf-8'))

def format_message_for_display(msg_data: dict) -> str:
    """Format a message dictionary for display"""
    if msg_data["type"] == "system":
        return f"[{msg_data['timestamp']}] System: {msg_data['content']}"
    else:
        return f"[{msg_data['timestamp']}] {msg_data['username']}: {msg_data['content']}" 

def create_handshake_message(msg_type: MessageType) -> bytes:
    """Create a simple handshake message"""
    return json.dumps({
        "type": msg_type.value,
        "content": msg_type.value.upper()  # e.g., "HELLO", "HELLO_ACK"
    }).encode('utf-8')

def log_error(error_type: str, details: str):
    """Log error messages"""
    logging.error(f"Error ({error_type}): {details}")