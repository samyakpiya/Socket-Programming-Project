import socket
import os
import os.path as osp
import pathlib
from datetime import datetime, timezone
from tabulate import tabulate
import time
import threading

SIZE = 1024
HOST = "localhost"
PORT = 6061
HEADER = 64
FORMAT = 'utf-8'
THREADLOCK = threading.Lock()


# if request is gotten from the server, then send the file to the server
def uploadToServer(filename, client):
    os.chdir(pathlib.Path(__file__).parent.absolute())
    if osp.exists(filename):
        print(f"[CLIENT] Uploading '{filename}'")
        s = f"UPLOAD@{filename}@{osp.getsize(filename)}"
        client.send(s.encode(FORMAT))
        with open(filename, 'rb') as f:
            while (bytes_out := f.read(SIZE)):
                client.send(bytes_out)


def downloadFromServer(filename, client):
    CLIENT_PATH = pathlib.Path(__file__).parent.absolute()
    stuff, *things = client.recv(SIZE).decode(FORMAT).split("@")
    with open(osp.join(CLIENT_PATH, filename), 'wb') as f:
        bytes_left = int(things[1])
        while bytes_left:
            bytes_in = client.recv(min(SIZE, bytes_left))
            f.write(bytes_in)
            bytes_left -= len(bytes_in)


def listening_thread(client: socket) -> None:
    while True:
        command, message = client.recv(SIZE).decode(FORMAT).split("@")
        THREADLOCK.acquire()
        if command == "UPLOAD":
            print("its going here")
            filename = message
            uploadToServer(filename, client)

        if command == "UPLOAD2":
            print("now its here")
            print(f"[CLIENT] Uploading '{message}'")
            s = f"UPLOAD@{message}@{osp.getsize(message)}"
            client.send(s.encode(FORMAT))

        if command == "DOWNLOAD":
            filename = message
            print(filename)
            downloadFromServer(filename, client)

        if command == "DOWNLOAD2":
            print("now its here")
            print(f"[CLIENT] Downloading '{message}'")
            s = f"DOWNLOAD@{message}"
            client.send(s.encode(FORMAT))
        elif command == "DIR" or command.lower() == "dir":
            newmsg = message
            print(newmsg)
            # print(tabulate(newmsg, headers=["Name", "Size (in bytes)", "Upload Date & Time", "Number of Downloads"]))
            print("Client: Enter command> ")
            continue
        else:
            print("Client: Enter command> ")
        THREADLOCK.release()


def main():
    connected = 0
    client = socket.socket()
    print("Client: welcome")
    # if its not connected, then ask for the user to enter the ip and port using the command CONNECT else tell them to connect again
    if connected == 0:
        connect, *info = input("Enter command> ").split(" ")
        if connect.lower() == "connect":
            ADDR = (info[0], int(info[1]))
            client.connect(ADDR)
            connected = 1
            print("Client: connected")
            client.send("ACK".encode(FORMAT))
            client.recv(SIZE).decode(FORMAT)
        else:
            # if not connected try again
            print("Could not connect")
    listening_client_thread = threading.Thread(target=listening_thread, args=(client,))
    listening_client_thread.start()
    # while its connected, then ask for the user to enter the command or wait for the server to send a request
    while True:
        # make sure you are in thee right directory
        os.chdir(pathlib.Path(__file__).parent.absolute())
        command, *params = input("Client: Enter command> ").split(" ")
        if command.lower() == "hello":
            client.send("HELLO".encode(FORMAT))
        elif command.lower() == "upload":
            if osp.exists(params[0]):
                print(f"[CLIENT] Uploading '{params[0]}'")
                s = f"UPLOAD@{params[0]}@{osp.getsize(params[0])}"
                client.send(s.encode(FORMAT))
            else:
                print(f"[CLIENT] '{params[0]}' does not exist.")
                continue
        elif command.lower() == "quit":
            client.send(command.encode(FORMAT))
            break
        # download the file from the server by having the server upload it to the client directory
        elif command.lower() == "download":
            CLIENT_PATH = pathlib.Path(__file__).parent.absolute()
            s = f"DOWNLOAD@{params[0]}"
            client.send(s.encode(FORMAT))
        # If client wants to see the content of the server directory, send it to the client
        # in a table format that has "Name", "Size (in MB)", "Upload Date & Time", "Number of Downloads",
        elif command.lower() == "dir":
            client.send(command.encode(FORMAT))
        elif command.lower() == "delete":
            s = f"DELETE@{params[0]}"
            client.send(s.encode(FORMAT))
            continue
        else:
            print("Command not found")
            continue
    client.close()


if __name__ == "__main__":
    main()