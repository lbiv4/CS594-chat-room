from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
import threading
import sys
import re
from chat_classes import *

# a client protocol


class ChatClient(irc.IRCClient):
    """
    This class exists as a protocol for a chat client to connect to the chat server in server.py

    This code leverages code from Twisted Python and was inspired by the following skeleton example:
        https://twistedmatrix.com/documents/current/core/howto/clients.html
    However, a lot of the functionality in the base class (IRCClient) is unused in favor of simpler code that just reads and prints messages
    """
    delimiter = "\n"

    def __init__(self, prefix, debug):
        self.prefix = "!"
        self.debug = debug
        self.readingInput = False

    def connectionMade(self):
        print("connection made")
        self.sendLine("!open Open plz")

    def connectionLost(self, reason):
        print("connection with server lost - closing application")

    def parsemsg(self, input):
        if not input:
            return("", "unknown")
        prefix = self.prefix if input[0] == self.prefix else ""
        words = input.split()
        command = words[0].replace(prefix, "").lower()
        return (command, prefix, words[1:])

    def dataReceived(self, data):
        """
        Method invoked when data passed through connection.  Parses input into three parts - a prefix, a command, and a list of words

        """
        (command, prefix, content) = self.parsemsg(data)
        # Check prefix matches server
        if command == "unknown" or data.strip() == "":
            print("Unknown response from server")
            self.transport.loseConnection()
        elif command == "open" and prefix == "":
            self.prefix = data[0]
            self.sendLine("{}open Retying prefix {}".format(
                self.prefix, self.prefix))
        elif command == "close":
            self._printMessage(data)
            self.transport.loseConnection()
        else:
            self._printMessage(data)
            # Create a thread to read input while main prints messages
            if not self.readingInput:
                input = threading.Thread(target=self._pollInput)
                input.setDaemon(True)  # End thread upon exit
                input.start()

    def _pollInput(self):
        """
        Method called in a separate thread to take command inputs
        """
        self.readingInput = True  # Lock input so multiple threads not spawned
        d = raw_input(">> ")
        self.sendLine(d)
        self.readingInput = False  # Unlock input so new threads spawned

    def _printMessage(self, data):
        """
        Method to print responses from server
        """
        data = data.strip()
        # If debugging, remove command and prefix from server response
        if not self.debug:
            data = " ".join(data.split()[1:])
        if self.readingInput:
            print("\n{}".format(data))
        else:
            print("{}".format(data))


class ChatClientFactory(protocol.ClientFactory):
    """
    Factory for client
    """

    def __init__(self, prefix, debug):
        self.prefix = prefix
        self.showCommands = debug

    def buildProtocol(self, addr):
        return ChatClient(self.prefix, self.showCommands)

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed - goodbye!")
        if reactor.running:
            reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        if reactor.running:
            reactor.stop()


if __name__ == '__main__':
    prefix = "!"
    debug = False
    for arg in sys.argv:
        if re.search("^--prefix=.$", arg):
            prefix = arg[-1]
        elif arg == "--debug":
            debug = True
    f = ChatClientFactory(prefix, debug)
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()
