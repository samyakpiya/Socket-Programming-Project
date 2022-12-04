import socket
import threading
import os
import pathlib
import os.path as osp
from datetime import datetime, timezone
from tabulate import tabulate
import pickle
import json
import time

# Server IP and Port
HOST = socket.gethostbyname(socket.gethostname())
PORT = 6061
SIZE = 65535
TYPE = "utf-8"
global SERVER_PATH
connections = []
files = []


# Client-1 is requesting a text file from the server. The server should simply check to see if it has the requested text
# file, if yes, it will send it to the client-1, otherwise the server has to  make a request to client-2 to upload the
# file to the server. As soon as the server has the file from client-2, then it will send it to client-1. As soon as
# client-1 receives the file, it should send a simple ACK to the server confirming the reception of the file. When the server receives the ACK from client-1, it should delete the file because it is not an existing file on the server and the sever borrowed it from the other client. Note that if the requested file is already an existing file on the server, then the file should not be deleted after the request is served. The file will only be deleted if the server has borrowed it from a client. Your program should handle all of these automatically.

def upload(client_socket, params, SERVER_PATH):
    if not osp.exists(SERVER_PATH):
        os.mkdir(SERVER_PATH)
    with open(osp.join(SERVER_PATH, params[0]), 'wb') as f:
        bytes_left = int(params[1])
        while bytes_left:
            bytes_in = client_socket.recv(min(SIZE, bytes_left))
            f.write(bytes_in)
            bytes_left -= len(bytes_in)


def download(client_socket, params, SERVER_PATH):
    a = f"DDOWNLOAD@{params[0]}@{osp.getsize(osp.join(SERVER_PATH, params[0]))}"
    client_socket.send(a.encode(TYPE))
    print(osp.join(SERVER_PATH, params[0]))
    with open(osp.join(SERVER_PATH, params[0]), 'rb') as f:
        while (bytes_out := f.read(SIZE)):
            client_socket.send(bytes_out)
    print(f"File {params[0]} downloaded successfully!")


# Server will be realized through a process accepting an incoming connection and handling the commands or files coming
# from the client. Handling two clients is required. The server will be able to handle multiple clients, commands,
# and files at the same time.

# handle_client function will be used to handle the client connection. It will have commands CONNECT server_IP_address,
# server_port, UPLOAD filename, DOWNLOAD filename, DELETE filename, and DIR: returns the content of folder
def handle_client(client_socket, client_address):
    # Print client's request
    request = client_socket.recv(SIZE).decode(TYPE)
    print(f"Received from {client_address[0]}:{client_address[1]}: {request}")

    while True:
        entry, *params = client_socket.recv(SIZE).decode(TYPE).split("@")
        print(entry, params)
        if entry == "HELLO":
            print("Server: cool")
        # If client1 wants to upload a file, upload it to the server directory
        elif entry == "UPLOAD":
            sending = f"UPLOAD@{params[0]}"
            client_socket.send(sending.encode(TYPE))
            SERVER_PATH = osp.join(pathlib.Path(__file__).parent.absolute(), "server")
            if osp.exists(SERVER_PATH):
                print("chicken")
                newentry, *params1 = client_socket.recv(SIZE).decode(TYPE).split("@")
                upload(client_socket, params1, SERVER_PATH)
            else:
                print("File does not exist")
                continue
        # If client wants to download a file, upload it to the client directory. If it does not exist,
        # ask client2 to upload the file to the server, and then send the file to the client,
        # after that delete the file from the server
        elif entry == "DOWNLOAD":
            filename = params[0]
            SERVER_PATH = osp.join(pathlib.Path(__file__).parent.absolute(), "server")
            if osp.exists(osp.join(SERVER_PATH, params[0])):
                sending = f"DOWNLOAD@{filename}"
                client_socket.send(sending.encode(TYPE))
                download(client_socket, params, SERVER_PATH)
            else:
                # if the file does not exist, ask client2 to upload the file to the server
                if client_socket == connections[0]:
                    sending = f'UPLOAD2@{filename}'
                    connections[1].send(sending.encode(TYPE))
                    time.sleep(2)
                    print(filename)
                    sending = f'DOWNLOAD2@{filename}'
                    connections[0].send(sending.encode(TYPE))

                elif client_socket != connections[0]:
                    sending = f'UPLOAD2@{filename}'
                    connections[0].send(sending.encode(TYPE))
                    time.sleep(2)
                    print(filename)
                    sending = f'DOWNLOAD2@{filename}'
                    connections[1].send(sending.encode(TYPE))
                else:
                    print(f"[SERVER] '{params[0]}' does not exist.")
                    continue

        # If client wants to delete a file, delete it from the server directory
        elif entry == "DELETE":
            SERVER_PATH = osp.join(pathlib.Path(__file__).parent.absolute(), "server")
            if not osp.exists(SERVER_PATH):
                os.mkdir(SERVER_PATH)
            os.remove(osp.join(SERVER_PATH, params[0]))
            print(f"File {params[0]} deleted successfully!")
        # If client wants to see the content of the server directory, send it to the client
        # in a table format that has "Name", "Size (in MB)", "Upload Date & Time", "Number of Downloads",
        elif entry == "DIR":
            SERVER_PATH = osp.join(pathlib.Path(__file__).parent.absolute(), "server")
            if not osp.exists(SERVER_PATH):
                os.mkdir(SERVER_PATH)
            files = os.listdir(SERVER_PATH)
            files_info = []
            for file in files:
                file_path = osp.join(SERVER_PATH, file)
                file_size = osp.getsize(file_path)
                file_date = datetime.fromtimestamp(osp.getmtime(file_path), timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
                file_downloads = 0
                files_info.append([file, file_size, file_date, file_downloads])
            print(files_info)
            table = tabulate(files_info,
                             headers=["Name", "Size (in bytes)", "Upload Date & Time", "Number of Downloads"])
            print(table)
            client_socket.send(f"DIR@{files_info}".encode(TYPE))
        # If client wants to disconnect, close the connection with that client
        elif entry == "QUIT":
            print(f"{client_address[0]}:{client_address[1]} Disconnected!")
            break


def main():
    # make sure you are in the righ directory
    os.chdir(pathlib.Path(__file__).parent.absolute())

    print("welcome to the server")
    # Create a socket object
    s = socket.socket()

    # Bind the socket to the IP and Port
    s.bind((HOST, PORT))

    # Listen for incoming connections
    s.listen(5)
    print(f"Listening as {HOST} {PORT} ...")

    while True:
        # Accept new connection
        client_socket, client_address = s.accept()
        client_socket.send("ACK".encode(TYPE))
        connections.append(client_socket)
        print(f"{client_address[0]}:{client_address[1]} Connected!")
        # Handle client in a separate thread
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()
        # keep track of how many clients are connected to the server
        print(f"Active Connections: {threading.activeCount() - 1}")
        print(connections)


if __name__ == "__main__":
    main()