from twisted.internet import reactor, protocol, stdio
from twisted.words.protocols import irc
import threading
import sys
import subprocess
from chat_classes import *


def _getRepeatedChar(char, count):
    output = ""
    for i in range(count):
        output += char
    return output


# a client protocol

class ChatClient(irc.IRCClient):
    delimiter = "\n"

    def __init__(self):
        self.states = CHAT_STATES
        self.readingInput = False
        self.currentInput = ""
        self.writingOutput = False

    def connectionMade(self):
        print("connection made")

    def connectionLost(self, reason):
        print("connection with server lost - closing application")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line:
            return
        line = line.decode("ascii")
        # print("Line: {}".format(line))

    def dataReceived(self, data):
        # print("here: {}".format(data))
        # print(self.transport)
        # print(self.serverTransport)
        # print("transports ^^^^^")
        self._printMessage(data)
        if not self.readingInput:
            input = threading.Thread(target=self._pollInput)
            input.start()

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
        """https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/"""


# def main():
if __name__ == '__main__':
    f = ChatClientFactory()
    # stdio.StandardIO(ChatClient(f.buildProtocol(None)))
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()
