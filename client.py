import socket
import threading

HOST = '127.0.0.1'
PORT = 8000

def receive_message():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:  # Check if message is not empty
                print(message)
            else:
                print("Disconnected from server.")
                break
        except Exception as e:
            print(f"Error occurred: {e}")
            client_socket.close()
            break

def send_message():
    while True:
        # User message
        message = input("")
        if message.lower() == "/exit":
            client_socket.close()
            print("Disconnected from the server.")
            break
        client_socket.send(message.encode('utf-8'))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect((HOST, PORT))
    print(f"Connected to the server at HOST:{HOST} PORT: {PORT}")
except:
    print("Unable to connect to the server.")
    exit()

# Start a thread to receive messages
receive_thread = threading.Thread(target=receive_message)
receive_thread.start()

# Start a thread to send messages
send_thread = threading.Thread(target=send_message)
send_thread.start()
