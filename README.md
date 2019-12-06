#CS594-chat-room

This is Lane Barton's IRC client/server implementation as part of the CS 594 final project. This project uses Twisted Python - see file documentation for an explanation

## File Overview

1. [chat_classes.py](./chat_classes.py) contains general helper functions
1. [server.py](./server.py) contains the server implementation
1. [client.py](./client.py) contains general helper functions

## How to Setup

This project is designed run with Python 2.7 on a Linux system and use `pip` and `virtualenv` to create a virtual environment for dependencies (namely Twisted Python). Assuming that this is setup, do the following to get started:

1. Clone this repository
2. Run `python2.7 -m virtualenv venv` and `source venv/bin/activate` to setup virtual environment
3. Run `pip install -r requirements.txt` to install Twisted Python
4. Follow steps to either [run a server](#running-the-server) or [run a client](#running-a-client)
5. When done, use `deactivate` to close virtual environment

## Running the Server

Assuming you have completed the setup steps and port 8000 is not in use, do one of the following:

1. `python2.7 server.py` to run the server
1. `python2.7 server.py --prefix={}` to run the server using a single character prefix as part of the design protocol

## Running a Client

Assuming you have completed the setup steps and started a server, do the following in a new terminal:

1. `python2.7 client.py` to run the server
1. `python2.7 client.py --prefix={}` to run the client using a single character prefix as part of the design protocol
1. `python2.7 client.py --debug` to run the client with debugging. This shows the full commands from the server in addition to printing response messages
