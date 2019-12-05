import sys
import time

p = None
print("This is your client shell for the chat room")
while p != "exit" and p != "/exit":
    p = raw_input("Enter input: ")
    print("Sent: '{}'".format(p))
