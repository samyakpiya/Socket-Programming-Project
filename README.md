# P2P File Sharing using Socket Programming

This project implements a peer-to-peer (P2P) file-sharing system using Python's Socket Programming. The project allows two clients to connect to a server, upload, download, and delete files. The server is responsible for handling the incoming requests and files, while clients can issue commands for the server to execute.

## Dependencies
This script requires the following dependencies to be installed:

* socket
* threading
* os
* pathlib
* datetime
* tabulate
* pickle
* json
* time

These dependencies can be installed using pip.

## Usage
The server can be started by running the server.py script.

```bash
$ python server.py
```

Once the server is started, it waits for two clients to connect.

After both clients have connected, each client can upload, download, or delete files from the server.

### Commands
The following commands are supported by the server:

#### UPLOAD
To upload a file to the server, a client can use the following command:

```bash
UPLOAD@filename
```

This will upload the file with the given filename to the server. The file will be stored in a directory called server.

#### DOWNLOAD
To download a file from the server, a client can use the following command:

```bash
DOWNLOAD@filename
```

If the file with the given filename exists on the server, it will be downloaded to the client. If the file does not exist on the server, the server will ask the other client to upload the file and then download it to the requesting client.

#### DELETE
To delete a file from the server, a client can use the following command:

```bash
DELETE@filename
```

This will delete the file with the given filename from the server directory.

## Implementation Details
The server.py script is a multi-threaded program that listens for incoming client connections. Once two clients have connected to the server, the server handles incoming requests from the clients.

If a client requests a file that does not exist on the server, the server will ask the other client to upload the file to the server, and then download it to the requesting client.

The server stores files in a directory called server. If this directory does not exist, it will be created.
