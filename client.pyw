#LAN Controller by obwan02
#Client

import socket as s
import os
import json
import ctypes

IP = s.gethostbyname(os.environ['COMPUTERNAME'])

GLOBAL_PORT = 5555
PORT = 4567
class Command:

    @staticmethod
    def parse(msg):
        jsonData = json.loads(msg)
        command = jsonData['command']
        data = jsonData['data']

        return Command(command, data)
    
    def __init__(self, command, data):
        assert type(command) == str
        assert type(data) == dict

        assert command in Command.commands
        
        self.command = command
        self.data = data

    def getJSON(self):
        jsonData = {
            'command' : self.command,
            'data' : self.data
            }
        
        return json.dumps(jsonData)

    def run(self):
        Command.commands[self.command](self.data)

Command.commands = {'MOUSE' : lambda a: mouseCommand(a), 'KEYBOARD' : lambda a: keyboardCommand(a)}

def mouseCommand(data):
    x = data['x']
    y = data['y']
    print(x, y)
    ctypes.windll.user.SetCursorPos(x, y)
    

def keyboardCommand(data):
    print(data)

class ControllerHandler:
    def __init__(self, ip, port):
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.sock.connect((ip, port))
        self.sock.send(b'CONNECT')

    def onMessageRecv(self, msg):
        msg = msg.decode('utf-8')
        command = Command.parse(msg)
        command.run()

    def listen(self):
        msg = self.sock.recv(2048)
        self.onMessageRecv(msg)
        

        
        
def listenForController():
    globalListen = s.socket(s.AF_INET, s.SOCK_DGRAM)
    globalListen.bind(('', GLOBAL_PORT))
    msg, cpu = globalListen.recvfrom(1024)
    globalListen.close()

    return cpu[0]
#For each connection session
while True:
    ip = listenForController()
    handler = ControllerHandler(ip, PORT)

    while True:
        handler.listen()
    #Once recieved connection session has started, and you have ip


