from twisted.internet import reactor, protocol, stdio
from twisted.words.protocols import irc
import threading
import sys
import subprocess
from chat_classes import *

# a client protocol


class ChatClient(irc.IRCClient):
    delimiter = "\n"

    def __init__(self):
        self.prefix = "!"
        self.readingInput = False
        self.currentInput = ""
        self.writingOutput = False

    def connectionMade(self):
        print("connection made")
        self.sendLine("!open Open plz")

    def connectionLost(self, reason):
        print("connection with server lost - closing application")

    def dataReceived(self, data):
        (command, prefix, content) = self.parsemsg(data)
        # Check prefix matches server
        if command == "open" and prefix == "":
            self.prefix = data[0]
            self.sendLine("{}open Retying prefix".format(self.prefix))
        else:
            self._printMessage(data)
            if not self.readingInput:
                input = threading.Thread(target=self._pollInput)
                input.setDaemon(True)
                input.start()

    def parsemsg(self, input):
        if not input:
            return("", "unknown")
        prefix = self.prefix if input[0] == self.prefix else ""
        words = input.split()
        command = words[0].replace(prefix, "").lower()
        print("Parse: {} / {} / {}".format(command, prefix, words[1:]))
        return (command, prefix, words[1:])

    def _pollInput(self):
        self.readingInput = True
        d = raw_input(">> ")
        self.sendLine(d)
        self.readingInput = False

    def _printMessage(self, data):
        data = data.strip()
        if self.readingInput:
            print("\n{}".format(data))
        else:
            print("{}".format(data))


class ChatClientFactory(protocol.ClientFactory):
    protocol = ChatClient

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed - goodbye!")
        if reactor.running:
            reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        if reactor.running:
            reactor.stop()


# def main():
if __name__ == '__main__':
    f = ChatClientFactory()
    # stdio.StandardIO(ChatClient(f.buildProtocol(None)))
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()
