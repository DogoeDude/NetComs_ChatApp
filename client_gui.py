import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QLabel, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import socket
import json
from protocol import (
    MessageType, create_message, parse_message, format_message_for_display,
    create_handshake_message, setup_logging, ConnectionStatus, log_connection_status,
    log_error
)

class ChatThread(QThread):
    message_received = pyqtSignal(str)
    connection_error = pyqtSignal(str)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.running = True

    def run(self):
        while self.running:
            try:
                # Set a timeout so we can check running state regularly
                self.client_socket.settimeout(0.1)  # 100ms timeout
                message = self.client_socket.recv(1024)
                
                if not self.running:
                    break
                    
                if message:
                    msg_data = parse_message(message)
                    formatted_message = format_message_for_display(msg_data)
                    self.message_received.emit(formatted_message)
                else:
                    break
                    
            except socket.timeout:
                continue  # Just check running state again
            except Exception as e:
                if self.running:  # Only emit error if not shutting down
                    self.connection_error.emit(f"Error occurred: {e}")
                break

    def stop(self):
        self.running = False

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.username = None
        self.chat_thread = None
        self.initUI()
        self.connectToServer()

    def initUI(self):
        self.setWindowTitle('Local Chat')
        self.setMinimumSize(800, 600)

        # Add menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        
        # Add quit action
        quitAction = fileMenu.addAction('Quit')
        quitAction.setShortcut('Ctrl+Q')
        quitAction.triggered.connect(self.close)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-family: Arial;
                font-size: 14px;
            }
        """)
        # Ensure word wrap is enabled
        self.chat_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        # Set a minimum height
        self.chat_display.setMinimumHeight(300)
        layout.addWidget(self.chat_display)

        # Display welcome message and commands
        welcome_message = """
Welcome to NetComs Chat!

Available Commands:
/help    - Display this help message
/exit    - Exit the chat
/clear   - Clear the chat window
/users   - Show online users (if supported)

Press Enter or click Send to send a message.
------------------------------------------
"""
        self.chat_display.append(welcome_message)

        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
                font-family: Arial;
                font-size: 14px;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Status bar
        self.statusBar().showMessage('Connecting...')

    def connectToServer(self):
        HOST = '127.0.0.1'
        PORT = 8000

        # Get username
        username, ok = QInputDialog.getText(self, 'Username', 'Enter your username:')
        if not ok or not username:
            self.close()
            return
        self.username = username

        # Connect to server
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            
            # Handshake process
            log_connection_status(ConnectionStatus.HANDSHAKE_STARTED)
            hello_msg = create_handshake_message(MessageType.HELLO)
            self.client_socket.send(hello_msg)
            
            response = parse_message(self.client_socket.recv(1024))
            if response["type"] != MessageType.HELLO_ACK.value:
                raise Exception("Handshake failed")
                
            username_msg = create_message(MessageType.USERNAME, self.username, self.username)
            self.client_socket.send(username_msg)
            
            response = parse_message(self.client_socket.recv(1024))
            if response["type"] != MessageType.USERNAME_ACK.value:
                raise Exception("Username not accepted")

            # Send join message
            join_message = create_message(MessageType.JOIN, self.username, "joined the chat")
            self.client_socket.send(join_message)

            # Start receive thread
            self.chat_thread = ChatThread(self.client_socket)
            self.chat_thread.message_received.connect(self.display_message)
            self.chat_thread.connection_error.connect(self.handle_connection_error)
            self.chat_thread.start()

            self.statusBar().showMessage('Connected')

        except Exception as e:
            QMessageBox.critical(self, 'Connection Error', f'Could not connect to server: {str(e)}')
            self.close()

    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            # Command handling
            if message.startswith('/'):
                self.handle_command(message.lower())
                self.message_input.clear()
                return
                
            try:
                chat_message = create_message(MessageType.CHAT, self.username, message)
                self.client_socket.send(chat_message)
                
                # Display our own message locally
                msg_data = parse_message(chat_message)
                formatted_message = format_message_for_display(msg_data)
                
                # Force GUI update
                QApplication.processEvents()
                self.display_message(formatted_message)
                self.message_input.clear()
                
            except Exception as e:
                print(f"Error in send_message: {e}")
                self.statusBar().showMessage(f'Error sending message: {str(e)}')

    def handle_command(self, command):
        if command == '/help':
            help_message = """
Available Commands:
/help    - Display this help message
/exit    - Exit the chat
/clear   - Clear the chat window
/users   - Show online users (if supported)
"""
            self.chat_display.append(help_message)
        
        elif command == '/exit':
            self.close()
        
        elif command == '/clear':
            self.chat_display.clear()
            self.chat_display.append("Chat cleared. Type /help for available commands.")
        
        elif command == '/users':
            # This would need server support to implement
            self.chat_display.append("Server does not support user listing yet.")
        
        else:
            self.chat_display.append(f"Unknown command: {command}")

    def display_message(self, message):
        """Update the chat display with new messages"""
        if not message:
            return
            
        try:
            self.chat_display.append(message)
            # Force update
            self.chat_display.repaint()
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"Error displaying message: {e}")

    def handle_connection_error(self, error_message):
        self.statusBar().showMessage(error_message)
        QMessageBox.warning(self, 'Connection Error', error_message)

    def closeEvent(self, event):
        if self.client_socket and self.chat_thread:
            try:
                # 1. Set running to False to stop the thread gracefully
                self.chat_thread.running = False
                
                # 2. Send leave message before closing anything
                leave_message = create_message(MessageType.LEAVE, self.username, "left the chat")
                self.client_socket.send(leave_message)
                
                # 3. Small delay to allow message to be sent
                self.chat_thread.wait(100)  # Wait 100ms
                
                # 4. Close socket
                try:
                    self.client_socket.shutdown(socket.SHUT_WR)  # Only shutdown writing
                except:
                    pass  # Socket might already be partially closed
                    
                self.client_socket.close()
                
                # 5. Wait for thread to finish
                self.chat_thread.wait()
                
            except Exception as e:
                print(f"Shutdown notice: {e}")  # Changed from error to notice
                
        event.accept()

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look across platforms
    chat_window = ChatWindow()
    chat_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 