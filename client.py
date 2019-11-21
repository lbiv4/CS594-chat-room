from twisted.internet import reactor, protocol, stdio
from twisted.words.protocols import irc
import copy


# a client protocol

class ChatClient(irc.IRCClient):
    delimiter = "\n"

    def __init__(self):
        self.pollingInput = False

    def connectionMade(self):
        print("connection made")

    def connectionLost(self, reason):
        print("connection lost")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line:
            return
        line = line.decode("ascii")
        #print("Line: {}".format(line))

    def dataReceived(self, data):
        #print("here: {}".format(data))
        # print(self.transport)
        # print(self.serverTransport)
        #print("transports ^^^^^")
        print("Received: {}".format(data))
        if not self.pollingInput:
            self.pollInput()

    def pollInput(self):
        self.pollingInput = True
        d = raw_input("Try this:")
        print("raw: {}".format(d))
        self.sendLine(d)
        self.pollingInput = False


class ChatClientFactory(protocol.ClientFactory):
    protocol = ChatClient

    def clientConnectionFailed(self, connector, reason):
        #print("Connection failed - goodbye!")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        #print("Connection lost - goodbye!")
        reactor.stop()


# def main():
if __name__ == '__main__':
    f = ChatClientFactory()
    # stdio.StandardIO(ChatClient(f.buildProtocol(None)))
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()
