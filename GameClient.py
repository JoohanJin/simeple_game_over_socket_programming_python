import socket

# Server configuration
HOST = 'localhost'
PORT = 12345

# Create a socket and connect to the server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Function to receive and display server responses
def receive_response():
    response = client_socket.recv(1024).decode().strip()
    print(response)
    return response

while True:
    server = receive_response()
    # condition for server
    if server.startswith("4001"): # terminating the client
        break
    elif server.startswith("3011"):
        receive_response()
    user_input = input()
    client_socket.send(user_input.encode())