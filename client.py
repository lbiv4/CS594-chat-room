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
        print("connection lost")

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
        #d = raw_input("Try this:")
        self.currentInput = ""
        while True:
            char = sys.stdin.read(1)
            if char == "\n":
                break
            self.currentInput = self.currentInput + char
        self.currentInput = self.currentInput.strip()
        if len(self.currentInput) > 0:
            self.sendLine(self.currentInput)
        self.currentInput = ""
        #print(">> ")
        #print("raw: {}".format(d))
        #print("Test: {}".format(output))
        # self.sendLine(d)
        self.readingInput = False

    def _printMessage(self, data):
        print("curr: ".format(self.currentInput))
        charDiff = len(self.currentInput) - len(data)
        overwrite = charDiff+4 if charDiff > 0 else 4
        line = ">> {}{}\n".format(data, _getRepeatedChar(" ", overwrite))
        sys.stdout.write("\033[F"+line)
        sys.stdout.flush()
        sys.stdout.write(">> '"+self.currentInput+"'")


class ChatClientFactory(protocol.ClientFactory):
    protocol = ChatClient

    def clientConnectionFailed(self, connector, reason):
        # print("Connection failed - goodbye!")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        # print("Connection lost - goodbye!")
        reactor.stop()


# def main():
if __name__ == '__main__':
    f = ChatClientFactory()
    # stdio.StandardIO(ChatClient(f.buildProtocol(None)))
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()
