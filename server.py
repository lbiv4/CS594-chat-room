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
    def __init__(self, users, messageChains):
        self.states = CHAT_STATES
        self.users = users
        self.messageChains = messageChains
        self.user = None
        self.state = "LOGGED_OUT"

    def connectionMade(self):
        print("Connected to a user")
        # print(self. users, self.state)
        self.sendLine("Welcome!")

    def connectionLost(self, reason):
        if self.state == "LOGGED_OUT":
            print("Disconnected from a logged out client")
        else:
            print("Disconnected from user '{}'".format(self.user.name))
        self.logoutUser()
        self.sendLine("Exited")

    def parsemsg(self, input):
        print("parse input: {}".format(input))
        if not input:
            return("", "unknown")
        prefix = "!" if input[0] == "!" else ""
        words = input.split()
        command = words[0].replace(prefix, "").lower()
        print("Parse: {} / {} / {}".format(command, prefix, words[1:]))
        return (command, prefix, words[1:])

    def dataReceived(self, data):
        print("Received: {}".format(data))
        (command, prefix, params) = self.parsemsg(data)
        self.handleCommand(command, prefix, params)

    def handleCommand(self, command, prefix, params):
        print("handle: {}, {}, {}".format(command, prefix, params))
        if not command:
            self.unknownCommand("")
        elif prefix == "!":
            if command == "login":
                self.login(params)
            elif command == "logout" or command == "quit" or command == "exit":
                self.logout(params)
            elif command == "create":
                self.createRoom(params)
            elif command == "join":
                self.joinRoom(params)
            elif command == "im" or command == "dm" or command == "privmsg":
                self.joinIM(params)
            elif command == "msg" or command == "message":
                self.message(params)
            else:
                self.unknownCommand(command)
        else:
            self.sendLine("Need ! for command")

    # Protocols

    def unknownCommand(self, command):
        self.sendLine("Unrecognized command '{}'".format(command))

    def login(self, args):
        if self.state != "LOGGED_OUT":
            self.sendLine(
                "Already logged in - see /help for valid commands")
        elif len(args) < 2:
            self.sendLine(
                "Please enter a username and password, e.g. !login <username> <password>")
        else:
            name = args[0]
            password = args[1]
            if name in self.users:
                if self.users[name].active:
                    self.sendLine(
                        "User {} is already logged in".format(name))
                elif self.users[name].password != password:
                    self.sendLine("Invalid username/password".format(name))
                else:
                    self.state = "LOGGED_IN"
                    self.users[name].active = True
                    self.users[name].protocol = self
                    self.user = self.users[name]
                    self.sendLine(
                        "Login successful. Welcome to the chat room, {}!".format(name))
            else:
                self.users[name] = User(name, password)
                self.sendLine(
                    "Registering new user '{}'. Please login again to verify password".format(name))

    def logout(self, args):
        if self.state == "LOGGED_OUT":
            self.sendLine(
                "Please login first with: !login <username> <password>")
        else:
            self.logoutUser()
            self.sendLine(
                "Log out successful. Goodbye, {}!")

    def createRoom(self, args):
        if self.state == "LOGGED_OUT":
            self.sendLine(
                "Please login first with: !login <username> <password>")
        elif len(args) < 1:
            self.sendLine("Need to enter a room name to create")
        else:
            newRoom = args[0]
            if newRoom.lower().startswith("im"):
                self.sendLine(
                    "Sorry, rooms cannot start with 'IM' due to implementation details")
            elif not newRoom in self.messageChains:
                self.messageChains[newRoom] = MessageChain(newRoom)
                self.sendLine(
                    "Created new room '{}'!".format(newRoom))
            else:
                self.sendLine(
                    "Room '{}' already exists".format(newRoom))

    def joinRoom(self, args):
        if self.state == "LOGGED_OUT":
            self.sendLine(
                "Please login first with: !login <username> <password>")
        elif len(args) < 1:
            self.sendLine("Need to enter a room name to join")
        else:
            room = args[0]
            if room.lower().startswith("im_"):
                self.sendLine(
                    "Use /im to look at IM messages with other users")
            elif room in self.messageChains:
                self.removeUserFromRoom()
                self.addUserToRoom(room)
                self.state = "IN_ROOM"
                self.sendLine(
                    "Joined room '{}'!".format(room))
                for msg in self.messageChains[room].getMessages(10):
                    self.sendLine(m)
            else:
                self.sendLine(
                    "Cannot join unrecognized room '{}'".format(room))

    def message(self, args):
        if not (self.state == "IN_ROOM" or self.state == "IN_IM"):
            self.sendLine("Need to be in a room or private im to message")
        else:
            msg = " ".join(args).strip()
            if len(msg) == 0:
                self.sendLine("A message needs non-blank contents to be sent")
            elif self.user.room:
                messageLoc = self.messageChains[self.user.room]
                newMessage = Message(self.user.name, datetime.now(), msg)
                messageLoc.messages.append(newMessage)
                for user in messageLoc.users:
                    user.protocol.sendLine(newMessage.getFormatted())
            else:
                self.sendLine(
                    "Unsure of where to send message - try /join or /im first")

    def joinIM(self, args):
        if self.state == "LOGGED_OUT":
            self.sendLine(
                "Please login first with: !login <username> <password>")
        elif len(args) == 0:
            self.sendLine(
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
                    self.sendLine(
                        "Unable to IM unknown user '{}'".format(user))
            if allUsersExist:
                imName = "IM " + " ".join(users)
                if not imName in self.messageChains:
                    self.messageChains[imName] = MessageChain(imName)
                self.removeUserFromRoom()
                self.addUserToRoom(imName)
                self.state = "IN_IM"
                self.sendLine(
                    "Joined IMs between {}!".format(users))
                for msg in self.messageChains[imName].getMessages(10):
                    self.sendLine(msg.getFormatted())

    # Helper Methods
    def removeUserFromRoom(self):
        if self.user:
            roomName = self.user.room
            if roomName:
                room = self.messageChains[roomName]
                if room:
                    room.removeUser(self.user)
                self.user.room = None

    def addUserToRoom(self, roomName):
        if self.user:
            if roomName and (roomName in self.messageChains):
                self.messageChains[roomName].addUser(self.user)
                self.user.room = roomName

    def logoutUser(self):
        self.removeUserFromRoom()
        self.state = "LOGGED_OUT"
        if self.user:
            self.users[self.user.name].active = False
            self.users[self.user.name].protocol = None
            self.user = None


class ChatServerFactory(Factory):

    def __init__(self):
        self.users = {}
        self.messages = {}

    def buildProtocol(self, addr):
        print("Protocol built")
        return ChatServer(self.users, self.messages)


# def main():
if __name__ == '__main__':
    reactor.listenTCP(8000, ChatServerFactory())
    reactor.run()
