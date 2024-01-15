import socket
import threading
import random

# Todo List
# 1. get the user info from text file and save it as a dictionary or two lists or class watever
# 2. make the listening socket so it listens to the connection request
# 3. authentication using the passwd and username
# 4. manage the room

# Server Configuration and Configurations
HOST = 'localhost'
PORT = 12345
USER_INFO_FILE = 'UserInfo.txt'
NUMBER_OF_USERS = 10
NUMBER_OF_ROOMS = 5
LOBBY_COMMANDS = ["/list", "/enter", "/exit"]
GAME_COMMANDS = ["/guess"]
GUESS_OPTIONS = ["true", "false"]



# GLOBAL VARIABLE 
users = {}
rooms = [[], [], [], [], []]
room_stat = [[0,0], [0,0], [0,0], [0,0], [0,0]]
result_sent = [False, False, False, False, False]
lock_for_rooms = threading.Lock()
Lock = threading.Lock()
LockStat = threading.Lock()
userLock = threading.Lock()



# play_game function -> maybe a function for game playing using the flag
def play_game(room_indx):
    response1 = ""
    response2 = ""

    with lock_for_rooms:
        player1 = rooms[room_indx][0]
        player2 = rooms[room_indx][1]

    with LockStat:
        guess1 = room_stat[room_indx][0]
        guess2 = room_stat[room_indx][1]
    

    if guess1 == guess2:
        response1 = "3023 The result is a tie\n"
        response2 = "3023 The result is a tie\n"
    else:
        solution = random.randint(0, 1)
        if guess1 == GUESS_OPTIONS[solution]:
            response1 = "3021 You are the winner\n"
            response2 = "3022 You lost this game\n"
        else:
            response1 = "3022 You lost this game\n"
            response2 = "3021 You are the winner\n"

    if not result_sent[room_indx]:
        with Lock:
            player1.send(response1.encode())
            player2.send(response2.encode())
            result_sent[room_indx] = True


def authentication(client_socket):
    isAuthenticated = False
    # keep asking what the username and passwd is until user can get authenticated successfully
    with userLock:
        while not isAuthenticated:
            client_socket.send(b'Please input your user name:\n')
            user_name = client_socket.recv(1024).decode().strip()
            client_socket.send(b'Please input your password:\n')
            password = client_socket.recv(1024).decode().strip()

            if user_name in users and users[user_name] == password:
                isAuthenticated = True
                client_socket.send(b'1001 Authentication successful\n')
            else:
                client_socket.send(b'1002 Authentication successful\n')

## user_handling function
def handling_client(client_socket):
    # we need to manage each client
    authentication(client_socket)
    
    # client gets into the game hall
    while True:
        command = client_socket.recv(1024).decode().strip()
        command_list = command.split(" ")
        print(command_list)
        indx = -1

        if ((len(command_list) > 2) or (command_list[0] not in LOBBY_COMMANDS) or (command_list[0]!= LOBBY_COMMANDS[1] and len(command_list)!=1)) or (command_list[0] == LOBBY_COMMANDS[1] and len(command_list) != 2):
            client_socket.send(b'4002 Unrecognized message\n')
        else:
            if command_list[0] == LOBBY_COMMANDS[0]:
                room_data = f"3001 {len(rooms)} "
                for room in rooms:
                    room_data += str(len(room)) + ' '
                client_socket.send(room_data.encode())
            elif command_list[0] == LOBBY_COMMANDS[1]:
                    # need to acquire lock since the code is modifying the global variable
                    # first let's check if the room selected is full or not
                    room_id = command_list[1]
                    room_indx = int(room_id) - 1
                    if len(rooms[room_indx]) == 2:
                        client_socket.send(b'3013 The room is full\n')
                    else:
                        with lock_for_rooms:
                            rooms[room_indx].append(client_socket)
                        # start the game or wait
                        if len(rooms[room_indx]) < 2:
                            client_socket.send(b'3011 Wait\n')
                            indx = 0
                        else:
                            indx = 1
                        while (True): # implemented busy waiting... to wait for the room to be filled.
                            if (len(rooms[room_indx]) == 2):
                                break
                        client_socket.send(b'3012 Game started. Please guess true or false\n')

                        guess_list = client_socket.recv(1024).decode().split(" ")

                        while (len(guess_list)!=2) or guess_list[0] not in GAME_COMMANDS or guess_list[1] not in GUESS_OPTIONS:
                            client_socket.send(b'4002 Unrecognized message\n')
                            guess_list = client_socket.recv(1024).decode().split(" ")

                        with LockStat:
                            room_stat[room_indx][indx] = guess_list[1]

                        

                        if indx:
                            with lock_for_rooms:
                                while (room_stat[room_indx][0] == 0 or room_stat[room_indx][1] == 0):
                                    pass
                            play_game(room_indx)                    

                            with lock_for_rooms:
                                rooms[room_indx].clear()
                            with Lock:
                                result_sent[room_indx] = False
                            with LockStat:
                                room_stat[room_indx] = [0, 0]

            elif command == LOBBY_COMMANDS[2]:
                client_socket.send(b'4001 Bye bye\n')
                client_socket.close()
                break
    

def main():
    try:
        # get the user info from the textfile
        with open(USER_INFO_FILE, 'r') as file:
            for line in file:
                username, password = line.strip().split(':')
                users[username] = password

        # Need to handle the client with the threads
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(NUMBER_OF_USERS)

        print(f"Server is listening on {HOST}:{PORT}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"New connection from {addr[0]}:{addr[1]}")

            client_thread = threading.Thread(target=handling_client, args=(client_socket,))
            client_thread.start()
    except KeyboardInterrupt:
        server_socket.close() # when?


if __name__ == "__main__":
    main()