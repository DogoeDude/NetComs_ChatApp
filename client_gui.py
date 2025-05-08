import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QLabel, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QThreadPool, QRunnable
from PyQt6.QtGui import QFont, QColor
import socket
import logging
from datetime import datetime
from protocol import (
    MessageType, create_message, parse_message, format_message_for_display,
    create_handshake_message, setup_logging
)
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import queue

class MessageProcessor(QRunnable):
    """Parallel message processor for handling incoming messages"""
    def __init__(self, message, callback):
        super().__init__()
        self.message = message
        self.callback = callback

    def run(self):
        try:
            msg_data = parse_message(self.message)
            formatted_message = format_message_for_display(msg_data)
            self.callback(formatted_message)
        except Exception as e:
            print(f"Error processing message: {e}")

class ChatThread(QThread):
    message_received = pyqtSignal(str)
    connection_error = pyqtSignal(str)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.running = True
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(multiprocessing.cpu_count() * 2)
        self.message_queue = queue.Queue()

    def run(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024)
                if message and self.running:
                    # Process message in parallel
                    processor = MessageProcessor(message, self.message_received.emit)
                    self.thread_pool.start(processor)
            except Exception as e:
                if self.running:
                    print(f"Thread error: {e}")
                    self.connection_error.emit(str(e))
                break

    def stop(self):
        self.running = False
        self.thread_pool.waitForDone()

class MessageSender(QRunnable):
    """Parallel message sender for handling outgoing messages"""
    def __init__(self, socket, message):
        super().__init__()
        self.socket = socket
        self.message = message

    def run(self):
        try:
            self.socket.send(self.message)
        except Exception as e:
            print(f"Error sending message: {e}")

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.username = None
        self.chat_thread = None
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(multiprocessing.cpu_count() * 2)
        self.initUI()
        self.connectToServer()

    def initUI(self):
        self.setWindowTitle('LoChat')
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 20px;
                padding: 10px;
                font-size: 14px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #0084ff;
            }
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0073e6;
            }
            QLabel {
                color: #0084ff;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #888888;
            }
            QMessageBox {
                background-color: #2d2d2d;
                color: #ffffff;
            }
        """)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Title
        title = QLabel("LoChat")
        title.setStyleSheet("""
            QLabel {
                color: #0084ff;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(title)

        # Chat display with rich text support
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setAcceptRichText(True)  # Enable rich text
        layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)

        # Status bar
        self.statusBar().showMessage('Not Connected')
        
        # Welcome message
        welcome_text = """
<span style="color: #0084ff;">Welcome to NetComs Chat!</span>

<span style="color: #888888;">Available Commands:
/help    - Display this help message
/exit    - Exit the chat
/clear   - Clear the chat window

Press Enter or click Send to send a message.</span>
------------------------------------------
"""
        self.chat_display.append(welcome_text)

    def connectToServer(self):
        HOST = '127.0.0.1'
        PORT = 8000

        # Get username
        username, ok = QInputDialog.getText(
            self, 'Login', 'Enter your username:',
            QLineEdit.EchoMode.Normal, ''
        )
        if not ok or not username:
            self.close()
            return
        self.username = username

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            
            # Log handshake steps
            logging.info(f"Attempting handshake for user {username}")
            
            # Parallel handshake process
            self._perform_handshake()
            
            # Start receive thread
            self.chat_thread = ChatThread(self.client_socket)
            self.chat_thread.message_received.connect(self.display_message)
            self.chat_thread.connection_error.connect(self.handle_connection_error)
            self.chat_thread.start()

            self.statusBar().showMessage('Connected')
            self.chat_display.append("Connected to server!")

        except Exception as e:
            logging.error(f"Connection error: {e}")
            QMessageBox.critical(self, 'Connection Error', f'Could not connect to server: {str(e)}')
            self.close()

    def _perform_handshake(self):
        """Perform handshake in parallel"""
        # Step 1: Send HELLO
        hello_msg = create_handshake_message(MessageType.HELLO)
        self.client_socket.send(hello_msg)
        logging.info("Sent HELLO message")
        
        # Step 2: Receive HELLO_ACK
        response = parse_message(self.client_socket.recv(1024))
        logging.info(f"Received response: {response}")
        if response["type"] != MessageType.HELLO_ACK.value:
            logging.error(f"Unexpected response during HELLO: {response}")
            raise Exception("Handshake failed")
        
        # Step 3: Send Username
        username_msg = create_message(MessageType.USERNAME, self.username, self.username)
        self.client_socket.send(username_msg)
        logging.info(f"Sent USERNAME: {self.username}")
        
        # Step 4: Receive USERNAME_ACK
        response = parse_message(self.client_socket.recv(1024))
        logging.info(f"Received username response: {response}")
        if response["type"] != MessageType.USERNAME_ACK.value:
            logging.error(f"Username not accepted: {response}")
            raise Exception("Username not accepted")

        # Send join message
        join_message = create_message(MessageType.JOIN, self.username, "joined the chat")
        self.client_socket.send(join_message)
        logging.info("Sent JOIN message")

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            if message.startswith('/'):
                self.handle_command(message)
            else:
                try:
                    chat_message = create_message(MessageType.CHAT, self.username, message)
                    # Send message in parallel
                    sender = MessageSender(self.client_socket, chat_message)
                    self.thread_pool.start(sender)
                    
                    # Display our own message immediately with highlighting
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    self.chat_display.append(
                        f'<div style="color: #00ff00;">'  # Bright green for own messages
                        f'[{timestamp}] {self.username}: {message}'
                        f'</div>'
                    )
                    
                    self.message_input.clear()
                except Exception as e:
                    print(f"Error sending message: {e}")
                    self.statusBar().showMessage(f'Error sending message: {str(e)}')

    def display_message(self, message):
        if self.username in message and "[System]" not in message:
            if f"{self.username}:" not in message:  # Not our message
                highlighted_message = message.replace(
                    self.username,
                    f'<span style="color: #00ff00;">{self.username}</span>'
                )
                self.chat_display.append(highlighted_message)
            else:
                self.chat_display.append(message)
        else:
            self.chat_display.append(message)

    def handle_command(self, command):
        if command == '/exit':
            self.close()
        elif command == '/clear':
            self.chat_display.clear()
            self.chat_display.append("Chat cleared. Type /help for available commands.")
        elif command == '/help':
            help_text = """
Available Commands:
/help    - Display this help message
/exit    - Exit the chat
/clear   - Clear the chat window
"""
            self.chat_display.append(help_text)

    def handle_connection_error(self, error_message):
        self.statusBar().showMessage(error_message)
        QMessageBox.warning(self, 'Connection Error', error_message)

    def closeEvent(self, event):
        try:
            if self.client_socket:
                # First stop the thread
                if self.chat_thread and self.chat_thread.isRunning():
                    self.chat_thread.running = False
                    self.chat_thread.wait(1000)  # Wait up to 1 second

                # Then send leave message
                try:
                    leave_message = create_message(MessageType.LEAVE, self.username, "left the chat")
                    sender = MessageSender(self.client_socket, leave_message)
                    self.thread_pool.start(sender)
                except:
                    pass  # Ignore send errors during shutdown

                # Finally close the socket
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass  # Socket might already be shutting down
                self.client_socket.close()

        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            event.accept()
            # Force quit if needed
            QApplication.quit()

def main():
    setup_logging()
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    chat_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 