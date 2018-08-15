#LAN Controller by obwan02
#Host

import socket as s
import json
import ctypes.wintypes
import ctypes
import time

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
        
        self.command = command
        self.data = data

    def getJSON(self):
        jsonData = {
            'command' : self.command,
            'data' : self.data
            }
        
        return json.dumps(jsonData)

class ClientHandler:
    def __init__(self):
        self.connect()

    def connect(self):
        listen = s.socket(s.AF_INET, s.SOCK_STREAM)
        listen.bind(('', PORT))
        listen.listen(1)
        sock, addr = listen.accept()
        listen.close()
        self.sock = sock
        
    def sendCommand(self, command):
        jsonData = command.getJSON()
        self.sock.send(jsonData.encode('utf-8'))

def connect():
    globalWrite = s.socket(s.AF_INET, s.SOCK_DGRAM)
    globalWrite.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)
    globalWrite.sendto(b'CONTROLLER:CONNECT', ('255.255.255.255', GLOBAL_PORT))
    globalWrite.close()

def getCursorPos():
    a = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(a))
    return a.x, a.y

connect()
client = ClientHandler()

x, y = getCursorPos()
while True:
    nx, ny = getCursorPos()
    if nx != x or ny != y:
        command = Command('MOUSE', {'x' : nx, 'y' : ny})
        client.sendCommand(command)
    x = nx
    y = ny
    time.sleep(0.1)


