class User:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.active = False
        self.rooms = []
        self.protocol = None


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

    def getFormattedMessages(self, numOfRecent):
        formattedMessages = []
        for msg in self.getMessages(numOfRecent):
            formattedMessages.append(msg.getFormatted())
        return formattedMessages

    def addMessage(self, message):
        if message:
            self.messages.push(message)

    def addUser(self, user):
        if not user in self.users:
            self.users.append(user)

    def removeUser(self, user):
        if user in self.users:
            self.users.remove(user)


class Message:
    def __init__(self, location, sender, time, text):
        self.location = location
        self.sender = sender
        self.time = time
        self.text = text

    def getFormatted(self):
        return "[{}]({})<{}>: {}".format(self.location, self.time.strftime("%m/%d/%Y@%H:%M:%S"), self.sender, self.text)
