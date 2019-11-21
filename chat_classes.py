
class User:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.active = True


class MessageChain:
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.users = []

    def getMessages(self, numOfRecent):
        if len(self.messages) <= numOfRecent:
            return self.messages
        else:
            return self.messages[(len(self.messages)-numOfRecent):]

    def addMessage(self, message):
        if message:
            self.messages.push(message)

    def addUser(self, user):
        if not name in self.users:
            self.users.push(user)

    def removeUser(self, user):
        if name in self.users:
            self.users.remove(user)


class Message:
    def __init__(self, sender, time, text):
        self.sender = sender
        self.time = time
        self.text = text

    def getFormatted(self):
        return "[{}]<{}>: {}".format(time, sender, text)
