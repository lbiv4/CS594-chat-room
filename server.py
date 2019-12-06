from twisted.internet import reactor, protocol
from twisted.words.protocols.irc import IRC
from twisted.internet.protocol import Factory
import threading
import sys
import re
from datetime import datetime
from chat_classes import *


class ChatServer(IRC):
    """
    This class exists as a protocol for a chat server to handle connections with multiple instances of the chat client in client.py

    This code leverages code from Twisted Python and was inspired from the following skeleton examples and documentation:
        https://twisted.readthedocs.io/en/twisted-17.9.0/core/howto/servers.html
        https://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.IRC.html
    However, the vast major of this code is specific to this project and doesn't follow the IRC protocol methods that closely. 
    """

    def __init__(self, expectedPrefix, users, messageChains):
        self.prefix = expectedPrefix
        self.users = users
        self.messageChains = messageChains
        self.user = None

    def connectionMade(self):
        print("Connected to a client")

    def connectionLost(self, reason):
        if not self.user or not self.user.active:
            print("Disconnected from a logged out client")
        else:
            print("Disconnected from user '{}'".format(self.user.name))
        self.logoutUser()
        self.sendResponse("close", "Confirming close, goodbye!")

    def parsemsg(self, input):
        """
        Parses input into three parts - a prefix, a command, and a list of words
        """
        if not input or input.strip() == "":
            return("", "unknown", input)
        prefix = self.prefix if input[0] == self.prefix else ""
        words = input.split()
        command = words[0].replace(prefix, "").lower()
        return (command, prefix, words[1:])

    def dataReceived(self, data):
        (command, prefix, params) = self.parsemsg(data)
        userInfo = self.user.name if self.user else "logged out client"
        print("Content from {}: {} / {} / {}".format(userInfo,
                                                     command, prefix, params))
        self.handleCommand(command, prefix, params)

    def handleCommand(self, command, prefix, params):
        """ Takes results of parsed message and hands control flow off to different command handlers accordingly

        Args:
            command(str): command that should be handled
            prefix(str): character indicating intent for a command from client
            params(List(str)): List of strings that get passed to handlers to process according to individual flows
        """
        if not command:
            self.unknownCommand("")
        elif prefix == self.prefix:
            if command == "open":
                self.sendResponse(
                    "open", "Welcome to the chat program! Use {}login to get started".format(self.prefix))
            elif command in ["close", "logout", "quit", "exit"]:
                self.logout(params)
            elif command == "login":
                self.login(params)
            elif command == "create":
                self.createRoom(params)
            elif command == "join":
                self.joinRoom(params)
            elif command == "leave":
                self.leaveRoom(params)
            elif command == "list":
                self.listInfo(params)
            elif command in ["msg", "message"]:
                self.message(params)
            elif command == "im":
                self.joinIM(params)
            elif command == "privmsg":
                self.sendIM(params)
            else:
                self.unknownCommand(command)
        else:
            self.sendResponse(
                "error", "Need {} for command prefix".format(self.prefix))

    # Protocols

    def unknownCommand(self, command):
        self.sendResponse("error", "Unrecognized command '{}'".format(command))

    def listInfo(self, args):
        """
        Handler for list command. Looks for input formatted like one of the following
            !list users
            !list rooms
            !list users <room>

        Args:
                args(List(str)): List of str arguments

        Return:
            Outputs response to client based on following commands:
                !list users: Returns list command with message providing all users and their online status
                !list rooms: Returns list command with message providing all rooms
                !list users <room>: If <room> is a valid room, returns list command with message providing all users who have joined that room
                else: Appropriate error response
        """
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
        elif len(args) == 0:
            self.sendResponse(
                "error", "Listing requires at least one argument. Use {}list <users|rooms>, e.g.".format(self.prefix))
        elif args[0].lower() == "rooms":
            rooms = []
            for room in self.messageChains.keys():
                # dont include IM "room"s
                if not room.startswith("IM"):
                    rooms.append(room)
            self.sendResponse(
                "list", "These are available rooms: {}".format(rooms))
        elif args[0].lower() == "users":
            if len(args) == 1:
                usersDict = {}
                for username in self.users:
                    usersDict[username] = self.users[username].active
                self.sendResponse(
                    "list", "These are registered users and their online status: {}".format(usersDict))
            elif len(args) == 2:
                targetRoom = args[1]
                if targetRoom in self.messageChains and (not targetRoom.lower().startswith("im")):
                    if not targetRoom in self.user.rooms:
                        self.sendResponse(
                            "error", "Please join room {} before attempting to view users")
                        return
                    usersInRoom = []
                    for user in self.messageChains[targetRoom].users:
                        usersInRoom.append(user.name)
                    self.sendResponse(
                        "list", "These are users that have joined the room '{}': {}".format(targetRoom, usersInRoom))
                else:
                    self.sendResponse("error", "Cannot recognize {} as room to command {}list users <room>".format(
                        targetRoom, self.prefix))
            else:
                self.sendResponse(
                    "error", "Too many arguments for {}list users <room> command".format(self.prefix))
        else:
            self.sendResponse(
                "error", "Invalid arguments for {}list command. Use {}list <users|rooms>, e.g.".format(self.prefix, self.prefix))

    def login(self, args):
        """
        Handler for login command. Looks for input formatted like `!login <username> <password>`. Creates the user with the provided name/password
        if the username is not stored on the server, logs the user in if username exists and the password matches

        Args:
                args(List(str)): List of str arguments.
                arg[0](str): username
                arg[1](str):password

        Return:
            Outputs create command upon registering a username/password combo, login command upon subsequent username/password match, error command otherwise
        """
        if self.userLoggedIn():
            self.sendResponse("error",
                              "Already logged in - see {}help for valid commands".format(self.prefix))
        elif len(args) < 2:
            self.sendResponse("error",
                              "Please enter a username and password, e.g. {}login <username> <password>".format(self.prefix))
        else:
            name = args[0]
            password = args[1]
            if name in self.users:
                if self.users[name].active:
                    self.sendResponse("error",
                                      "User {} is already logged in".format(name))
                elif self.users[name].password != password:
                    self.sendResponse(
                        "error", "Invalid username/password".format(name))
                else:
                    self.users[name].active = True
                    self.users[name].protocol = self
                    self.user = self.users[name]
                    self.sendResponse("login",
                                      "Login successful. Welcome to the chat room, {}!".format(name))
            else:
                self.users[name] = User(name, password)
                self.sendResponse("create",
                                  "Registering new user '{}'. Please login again to verify password".format(name))

    def logout(self, args):
        """
        Handler for logout command. Looks for input formatted like `!logout`.

        Args:
                args(List(str)): List of str arguments. Does not matter for this command

        Return:
            Outputs close command
        """
        self.logoutUser()
        self.sendResponse("close",
                          "Log out successful. Goodbye!")

    def createRoom(self, args):
        """
        Handler for create command to create a room. Looks for input formatted like `!create <roomname>` where the room name cannot
        contain the prefix, | character, or start with "im" due to other implementation details

        Args:
                args(List(str)): List of str arguments. Should contain a single value corresponding to a room name

        Return:
            Outputs create command upon registering a new room, error command otherwise
        """
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
        elif len(args) < 1:
            self.sendResponse("error", "Need to enter a room name to create")
        else:
            newRoom = args[0]
            if newRoom.lower().startswith("im"):
                self.sendResponse("error",
                                  "Sorry, rooms cannot start with 'IM' due to implementation details")
            elif ("|" in newRoom) or (self.prefix in newRoom):
                self.sendResponse("error",
                                  "Sorry, rooms cannot contain the characters {} or {} due to implementation details".format("|", self.prefix))
            elif not newRoom in self.messageChains:
                self.messageChains[newRoom] = MessageChain(newRoom)
                self.sendResponse("create",
                                  "Created new room '{}'!".format(newRoom))
            else:
                self.sendResponse("error",
                                  "Room '{}' already exists".format(newRoom))

    def joinRoom(self, args):
        """
        Handler for join command to join a room. Looks for input formatted like `!join <roomname>` where the room name corresponds to a created room

        Args:
                args(List(str)): List of str arguments. Should contain a single value corresponding to a room name

        Return:
            Outputs join command upon joining an existing room that the user was not previously in, error otherwise
        """
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
        elif len(args) < 1:
            self.sendResponse("error", "Need to enter a room name to join")
        else:
            room = args[0]
            if room.lower().startswith("im"):
                self.sendResponse("error",
                                  "Use {}im to look at IM messages with other users".format(self.prefix))
            elif room in self.messageChains:
                if not (room in self.user.rooms):
                    self.addUserToRoom(room)
                    self.sendResponse("join",
                                      "Joined room '{}'!".format(room))
                    for msg in self.messageChains[room].getFormattedMessages(10):
                        self.sendResponse("msg", msg)
                else:
                    self.sendResponse(
                        "error", "Already joined room '{}'".format(room))
            else:
                self.sendResponse("error",
                                  "Cannot join unrecognized room '{}'".format(room))

    def leaveRoom(self, args):
        """
        Handler for leave command to leave a room. Looks for input formatted like `!leave <roomname>` where the room name corresponds to a room the user has joined

        Args:
                args(List(str)): List of str arguments. Should contain a single value corresponding to a room name

        Return:
            Outputs leave command upon joining a room that the user had previously joined, error command otherwise
        """
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
        elif len(args) < 1:
            self.sendResponse(
                "error", "Need to enter at least one room name to leave")
        else:
            # check rooms for existance, if it is an IM "room", or if user is not in room. Send error accordingly
            for room in args:
                if (not room in self.messageChains) or room.lower().startswith("im"):
                    self.sendResponse(
                        "error", "Cannot recognize room '{}' to leave".format(room))
                    return
                elif not (room in self.user.rooms):
                    self.sendResponse(
                        "error", "Not currently in room '{}'.".format(room))
            for room in args:
                self.removeUserFromRoom(room)
                self.sendResponse("leave",
                                  "Left room '{}'!".format(room))

    def message(self, args):
        """Method to handle messages to one or more rooms. See sendIM for private messging

        Takes list of string that should be formatted like `< room1 > <room2 > ... < roomN > | message`.
        If properly formatted, will send the message contents to all rooms listed before the `|` divider

            Args:
                args(List(str)): List of str arguments
        """
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
            return
        targetRooms = []
        i = 0
        # Get list of rooms as initial terms, looking for | as divider
        while i < len(args) and not args[i].strip().startswith("|"):
            if not (args[i] in self.messageChains):
                self.sendResponse(
                    "error", "Cannot recognize room {} as parameter to a {}msg call".format(args[i], self.prefix))
                return
            # Check that user is in all rooms AND room is not an IM "room"
            elif not (args[i] in self.user.rooms) or args[i].lower().startswith("im"):
                self.sendResponse(
                    "error", "You cannot send a message to room {} because you have not joined".format(args[i]))
                return
            else:
                targetRooms.append(args[i])
                i = i+1

        # Get full message string including | divider
        msg = " ".join(args[i:]).strip()
        # remove | divider
        msg = msg[1:].strip()
        # Check for empty message
        if len(msg) == 0:
            self.sendResponse(
                "error", "A message needs non-blank contents to be sent")
        # Check for no rooms to target
        elif len(targetRooms) == 0:
            self.sendResponse("error"
                              "Unsure of where to send message - try {}join first".format(self.prefix))
        else:
            currTime = datetime.now()
            for target in targetRooms:
                newMessage = Message(target, self.user.name, currTime, msg)
                messageLoc = self.messageChains[target]
                messageLoc.messages.append(newMessage)
                for user in messageLoc.users:
                    user.protocol.sendResponse(
                        "msg", newMessage.getFormatted())

    def joinIM(self, args):
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
        elif len(args) == 0:
            self.sendResponse("error",
                              "Need to add users to IM like {}im <user1> <user2> ...".format(self.prefix))
        else:
            # Remove any duplicates
            users = list(dict.fromkeys(args))
            if not self.user.name in users:
                users.append(self.user.name)
            users.sort()
            allUsersExist = True
            for user in users:
                if not user in self.users:
                    allUsersExist = False
                    self.sendResponse("error",
                                      "Unable to IM unknown user '{}'".format(user))
            if allUsersExist:
                imName = "IM " + " ".join(users)
                if not imName in self.messageChains:
                    self.messageChains[imName] = MessageChain(imName)
                self.addUserToRoom(imName)
                self.sendResponse("im",
                                  "Joined IMs between {}!".format(users))
                for msg in self.messageChains[imName].getMessages(10):
                    self.sendResponse("msg", msg.getFormatted())

    def sendIM(self, args):
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: {}login <username> <password>".format(self.prefix))
            return
        targetUsers = []
        i = 0
        # Get list of users, looking for | as divider
        while i < len(args) and not args[i].strip().startswith("|"):
            if not (args[i] in self.users):
                self.sendResponse(
                    "error", "Cannot recognize user {} as parameter to a {}privmsg call".format(args[i], self.prefix))
                return
            else:
                targetUsers.append(args[i])
                i = i+1
        # Add user if not included
        if not self.user.name in targetUsers:
            targetUsers.append(self.user.name)
        # Get full message string including | divider
        msg = " ".join(args[i:]).strip()
        # remove | divider
        msg = msg[1:].strip()
        # Check for empty message
        if len(msg) == 0:
            self.sendResponse(
                "error", "A message needs non-blank contents to be sent")
        # Check for no users or just sending user
        elif len(targetUsers) <= 1:
            self.sendResponse("error",
                              "Unsure of who to send private massage - make sure there is one user beside yourself listed".format(self.prefix, self.prefix))
        else:
            targetUsers.sort()
            imName = "IM {}".format(" ".join(targetUsers))
            newMessage = Message(imName, self.user.name, datetime.now(), msg)
            if self.messageChains.has_key(imName):
                messageLoc = self.messageChains[imName]
                messageLoc.messages.append(newMessage)
                for user in messageLoc.users:
                    user.protocol.sendResponse(
                        "msg", newMessage.getFormatted())
            else:
                self.sendResponse("error", "Please start an IM chain first with {}im {}".format(
                    self.prefix, " ".join(targetUsers)))

    # Helper Methods

    def userLoggedIn(self):
        """
        Helper method to check if a user has sent a `login` command and logged in
        """
        return self.user and self.user.active

    def removeUserFromRoom(self, roomName):
        """
        Helper method to remove a user from a rooom if they had joined that room
        """
        if self.user:
            room = self.messageChains[roomName]
            if room and (roomName in self.user.rooms):
                room.removeUser(self.user)
                self.user.rooms.remove(roomName)

    def removeUserFromAllRooms(self):
        rooms = list(dict.fromkeys(self.user.rooms))
        for i in rooms:
            self.removeUserFromRoom(i)

    def addUserToRoom(self, roomName):
        """
        Helper method to add a user to a rooom if they had not previously joined that room
        """
        if self.user:
            if roomName and (roomName in self.messageChains and not (roomName in self.user.rooms)):
                self.messageChains[roomName].addUser(self.user)
                self.user.rooms.append(roomName)

    def logoutUser(self):
        """
        Helper method to handle logout and prepare for client disconnection by removing a user from all rooms and disassociating from a protocol
        """
        if self.user:
            self.removeUserFromAllRooms()
            self.users[self.user.name].active = False
            self.users[self.user.name].protocol = None
            self.user = None

    def sendResponse(self, command, params):
        """
        Helper method for formatting a command amd its associated message
        """
        userInfo = self.user.name if self.user else "logged out client"
        if params:
            output = "{}{} {}".format(
                self.prefix, command.lower(), params)
            self.sendLine(output)
            print("Response to {}: {}".format(userInfo, output))
        else:
            output = "{}{}".format(self.prefix, command.lower())
            self.sendLine(output)
            print("Response to {}: {}".format(userInfo, output))


class ChatServerFactory(Factory):
    """
    A factory class that takes the ChatSever protocol and holds state/listens to connection.
    """

    def __init__(self, prefix):
        self.prefix = prefix
        self.users = {}
        self.messages = {}

    def buildProtocol(self, addr):
        print("Protocol built")
        return ChatServer(self.prefix, self.users, self.messages)


if __name__ == '__main__':
    print("Starting server")
    prefix = "!"
    for arg in sys.argv:
        if re.search("^--prefix=.$", arg):
            prefix = arg[-1]
    reactor.listenTCP(8000, ChatServerFactory(prefix))
    reactor.run()
