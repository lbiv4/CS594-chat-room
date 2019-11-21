"""https://twisted.readthedocs.io/en/twisted-17.9.0/core/howto/servers.html"""
"""https://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.IRC.html#handleCommand
https://buildmedia.readthedocs.org/media/pdf/twisted/latest/twisted.pdf
https://twistedmatrix.com/documents/13.1.0/core/howto/clients.html
https://twistedmatrix.com/documents/current/api/twisted.protocols.basic.LineReceiver.html

"""

"""
States:
LOGGED_OUT
LOGGED_IN
IN_ROOM
IN_IM
"""




from twisted.internet import reactor, protocol
from twisted.words.protocols.irc import IRC
from twisted.internet.protocol import Factory
from chat_classes import *
class ChatServer(IRC):
    def __init__(self, users, messageChains):
        self.users = users
        self.messageChains = messageChains
        self.name = None
        self.state = "LOGGED_OUT"

    def connectionMade(self):
        print("Connected to a user")
        #print(self. users, self.state)
        self.sendMessage("Test")

    def connectionLost(self, reason):
        print("Disconnected from a user")
        self.sendMessage("Exited")

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
        print(data)
        print("Received: {}".format(data))
        # self.sendLine("Returned")
        (command, prefix, params) = self.parsemsg(data)
        self.handleCommand(command, prefix, params)

    def handleCommand(self, command, prefix, params):
        if not command:
            self.irc_unknown("")
        elif prefix == "!":
            if command == "login":
                self.irc_login(prefix, params)
            else:
                self.irc_unknown(command)
        else:
            self.sendMessage("Need ! for command")

    def irc_unknown(self, command):
        self.sendMessage("Unrecognized command '{}'".format(command))

    def irc_login(self, prefix, args):
        if self.state != "LOGGED_OUT":
            self.sendMessage(
                "Already logged in - see /help for valid commands")
        elif len(args) < 2:
            self.sendMessage(
                "Please enter a username and password, e.g. /login <username> <password>")
        else:
            name = args[0]
            password = args[1]
            if name in self.users:
                if self.users[name].active:
                    self.sendMessage(
                        "User {} is already logged in".format(name))
                elif self.users[name].password != password:
                    self.sendMessage("Invalid username/password".format(name))
                else:
                    self.users[name].active = True
                    self.sendMessage(
                        "Login successful. Welcome to the chat room, {}!".format(name))
            else:
                self.users[name] = User(name, password)
                self.sendMessage(
                    "Registering new user '{}'. Please login again to verify password".format(name))

        def irc_logout(self, prefix, args):
            if self.state == "LOGGED_OUT":
                self.sendMessage(
                    "Please login first with: /login <username> <password>")
            else:
                self.users[self.name].active = False
                self.name = None
                self.state = "LOGGED_OUT"
                self.sendMessage(
                    "Log out successful. Welcome to the chat room, {}!")


class ChatServerFactory(Factory):

    def __init__(self):
        self.users = {}
        self.messages = {}

    def buildProtocol(self, addr):
        return ChatServer(self.users, self.messages)


# def main():
if __name__ == '__main__':
    reactor.listenTCP(8000, ChatServerFactory())
    reactor.run()
