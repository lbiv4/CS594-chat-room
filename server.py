"""https://twisted.readthedocs.io/en/twisted-17.9.0/core/howto/servers.html"""
"""https://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.IRC.html#handleCommand
https://buildmedia.readthedocs.org/media/pdf/twisted/latest/twisted.pdf
https://twistedmatrix.com/documents/13.1.0/core/howto/clients.html
https://twistedmatrix.com/documents/current/api/twisted.protocols.basic.LineReceiver.html

"""




from twisted.internet import reactor, protocol
from twisted.words.protocols.irc import IRC
from twisted.internet.protocol import Factory
import threading
from datetime import datetime
from chat_classes import *
class ChatServer(IRC):
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
        if not input:
            return("", "unknown")
        prefix = self.prefix if input[0] == self.prefix else ""
        words = input.split()
        command = words[0].replace(prefix, "").lower()
        return (command, prefix, words[1:])

    def dataReceived(self, data):
        (command, prefix, params) = self.parsemsg(data)
        userInfo = self.user.name if self.user else "logged out client"
        print("Content from {}: {} / {} / {}".format(userInfo,
                                                     command, prefix, words[1:]))
        self.handleCommand(command, prefix, params)

    def handleCommand(self, command, prefix, params):
        if not command:
            self.unknownCommand("")
        elif prefix == self.prefix:
            if command == "open":
                self.sendResponse(
                    "open", "Welcome to the chat program! Use /login to get started")
            elif command in ["close", "logout", "quit", "exit"]:
                self.logout(params)
            elif command == "login":
                self.login(params)
            elif command == "create":
                self.createRoom(params)
            elif command == "join":
                self.joinRoom(params)
            elif command == "im":
                self.joinIM(params)
            elif command in ["msg", "message"]:
                self.message(params)
            else:
                self.unknownCommand(command)
        else:
            self.sendResponse(
                "error", "Need {} for command prefix".format(self.prefix))

    # Protocols

    def unknownCommand(self, command):
        self.sendResponse("error", "Unrecognized command '{}'".format(command))

    def login(self, args):
        if self.userLoggedIn():
            self.sendResponse("error",
                              "Already logged in - see /help for valid commands")
        elif len(args) < 2:
            self.sendResponse("error",
                              "Please enter a username and password, e.g. !login <username> <password>")
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
                self.sendResponse("error",
                                  "Registering new user '{}'. Please login again to verify password".format(name))

    def logout(self, args):
        if self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: !login <username> <password>")
        else:
            self.logoutUser()
            self.sendResponse("close",
                              "Log out successful. Goodbye, {}!")

    def createRoom(self, args):
        if self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: !login <username> <password>")
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
        if not self.userLoggedIn():
            self.sendResponse("error",
                              "Please login first with: !login <username> <password>")
        elif len(args) < 1:
            self.sendResponse("error", "Need to enter a room name to join")
        else:
            room = args[0]
            if room.lower().startswith("im"):
                self.sendResponse("error",
                                  "Use /im to look at IM messages with other users")
            elif room in self.messageChains:
                self.addUserToRoom(room)
                self.sendResponse("join",
                                  "Joined room '{}'!".format(room))
                for msg in self.messageChains[room].getFormattedMessages(10):
                    self.sendResponse("msg", msg)
            else:
                self.sendResponse("error",
                                  "Cannot join unrecognized room '{}'".format(room))

    def message(self, args):
        """Method to handle messages to one or more rooms. See sendIM for private messging

        Takes list of string that should be formatted like < room1 > <room2 > ... < roomN > | message.
        If properly formatted, will send the message contents to all rooms listed before the | divider

            Args:
                param1(List(str)): List of str arguments
        """
        targetRooms = []
        i = 0
        # Get list of rooms as initial terms, looking for | as divider
        while i < len(args) and not args[i].strip().startswith("|"):
            if not (args[i] in self.messageChains):
                self.sendResponse(
                    "error", "Cannot recognize room {} as parameter to a /msg call".format(args[i]))
                return
            # Check that user is in all rooms AND room is not an IM "room"
            elif not (args[i] in self.user.rooms) or args[i].startswith("IM"):
                self.sendResponse(
                    "error", "You cannot send a message to room {} because you have not joined".format(args[i]))
                return
            else:
                targetRooms.append(args[i])

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
                              "Unsure of where to send message - try /join first")
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
                              "Please login first with: !login <username> <password>")
        elif len(args) == 0:
            self.sendResponse("error",
                              "Need to add users to IM like /im <user1> <user2> ...")
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

    """def sendIM(self, args):
        targetUsers = []
        let i = 0
        # Get list of users, looking for | as divider
        while i < len(args) and not args[i].strip().startswith("|"):
            if not (args[i] in self.users):
                self.sendResponse(
                    "error", "Cannot recognize user {} as parameter to a /privmsg call".format(args[i]))
                return;
            else:
                targetRooms.append(args[i])
        # Get full message string including | divider
        msg = " ".join(args[i:]).strip()
        # remove | divider
        msg = msg[1:].strip()
        # Check for empty message
        if len(msg) == 0:
            self.sendResponse(
                "error", "A message needs non-blank contents to be sent")
        # Check for no rooms to target
        elif len(targetUsers) == 0:
            self.sendResponse("error"
                                "Unsure of where to send message - try /join or /im first")
        else:"""

    # Helper Methods
    def userLoggedIn(self):
        return self.user and self.user.active

    def removeUserFromRoom(self, roomName):
        if self.user:
            room = self.messageChains[roomName]
            if room:
                room.removeUser(self.user)
            self.user.room = None

    def addUserToRoom(self, roomName):
        if self.user:
            if roomName and (roomName in self.messageChains and not (roomName in self.user.rooms)):
                self.messageChains[roomName].addUser(self.user)
                self.user.rooms.append(roomName)

    def logoutUser(self):
        if self.user:
            for room in self.user.rooms:
                self.removeUserFromRoom()
            self.users[self.user.name].active = False
            self.users[self.user.name].protocol = None
            self.user = None

    def sendResponse(self, command, params):
        if params:
            self.sendLine("{}{} {}".format(
                self.prefix, command.lower(), params))
        else:
            self.sendLine("{}{}".format(self.prefix, command.lower()))


class ChatServerFactory(Factory):

    def __init__(self):
        self.users = {}
        self.messages = {}

    def buildProtocol(self, addr):
        print("Protocol built")
        return ChatServer("!", self.users, self.messages)


# def main():
if __name__ == '__main__':
    reactor.listenTCP(8000, ChatServerFactory())
    reactor.run()
