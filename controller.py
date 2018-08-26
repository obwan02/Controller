#LAN Controller by obwan02
#Host

import socket as s
import json
import os
import ctypes.wintypes
import ctypes
import time
import winlib
import winlib.keyboard_funcs
import winlib.defs as defs
import sys
from threading import Thread
import tkinter as tk
from PIL.ImageTk import PhotoImage
import PIL.Image as Image
import pickle
import struct

GLOBAL_PORT = 5555
PORT = 4567
STREAM_PORT = 6555

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

class StreamHandler:

    def __init__(self, port):
        self.port = port
        self.frames = []

        server = s.socket(s.AF_INET, s.SOCK_STREAM)
        server.bind(('', port))
        server.listen(1)
        
        self.sock, addr = server.accept()
        self.thread = Thread(target=self.streamThread)
        self.thread.start()

    def setTarget(self, target):
        self.onFrameRecv = target

    def streamThread(self):
        time.sleep(1)
        extraData = b''
        frame = []
        current = None
        while True:
            data = b''
            try:
                data = extraData + self.sock.recv(8192)
            except ConnectionResetError:
                os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
                exit(2)
            extraData = b''
            i = data.find(b'END!')
            if i != -1:
                d = data[:i]
                extraData = data[(i + 4):]
                #self.frames.append(b''.join(frame) + d)
                final = b''.join(frame) + d
                a = pickle.loads(final)
                current = PhotoImage(a)
                self.onFrameRecv(image=current)     
                frame = []
            else:
                frame.append(data)

##    def get(self):
##        while len(self.frames) < 1:
##            print('Waiting...')
##        a = self.frames[0]
##        del self.frames[0]
##        return a

class ClientHandler:
    def __init__(self):
        self.connected = False
        #Connect thread should close after connection hasstarted
        self.connectThread = Thread(target=self.connect1)
        self.connectThread.start()
        self.connect2()
        del self.connectThread

        #Holds commands to be sent
        self.commandBuffer = []

    '''
    connect1 and connect2 run in parallel; one sends connection requests over the whole network,
    the other listens on the port for the client to connect. 
    '''

    #Sends connection requests over the network (10 times)
    #When client recieves, it connects to this
    #N.B. When client recieves this, it then connects to us, which then breaks the while loop
    def connect1(self):
        globalWrite = s.socket(s.AF_INET, s.SOCK_DGRAM)
        globalWrite.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)
        print('Trying to Connect...')
        print('Sending Connection Requests:\n')
        
        t = 1
        while not self.connected:
            if t == 1: print('One (', t, '/ 10 )')
            else: print('Another One (' , t, '/ 10 )')
            globalWrite.sendto(b'CONTROLLER:CONNECT', ('255.255.255.255', GLOBAL_PORT))
            if t == 10:
                print("\nCouldn't Connect")
                time.sleep(2)
                globalWrite.close()
                os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
                exit(2)
            time.sleep(2)
            t += 1
        globalWrite.close()
        
    #Wait for a connection from client
    #N.B. Client connects when it recieves the broadcast in connect1
    def connect2(self):
        listen = s.socket(s.AF_INET, s.SOCK_STREAM)
        listen.bind(('', PORT))
        listen.listen(1)
        sock, addr = listen.accept()
        listen.close()
        self.sock = sock
        self.connected = True
        self.streamer = StreamHandler(STREAM_PORT)
        
        self.windowThread = Thread(target=self.windowFunc)
        self.windowThread.start()
        
        print('\nConnected')

    def windowFunc(self):
        self.root = tk.Tk()
        self.root.resizable(width=False, height=False)
        self.root.protocol("WM_DELETE_WINDOW", exit)
        self.display = tk.Label(self.root, image=None)
        self.streamer.setTarget(self.display.configure)
        self.display.pack()
        self.root.mainloop()
            
        
        
    def sendCommand(self, command):
        self.commandBuffer.append(command)

    def loop(self):
        global hookManager
        while True:
            toRemove = []
            for command in self.commandBuffer:
                jsonData = command.getJSON()
                data = jsonData.encode('utf-8')
                
                length = len(data)
                lengthData = length.to_bytes(2, 'little')

                try:
                    self.sock.sendall(lengthData)
                    self.sock.sendall(data)
                    pass

                except ConnectionResetError:
                    hookManager.__del__()
                    os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
                    exit(2)
                toRemove.append(command)
            for i in toRemove:
                self.commandBuffer.remove(i)

        

mouseFunctions = { defs.WM_LBUTTONDOWN : defs.MOUSEEVENTF_LEFTDOWN, 
    defs.WM_LBUTTONUP : defs.MOUSEEVENTF_LEFTUP,
    defs.WM_MOUSEMOVE : defs.MOUSEEVENTF_ABSOLUTE,
    defs.WM_MOUSEWHEEL : defs.MOUSEEVENTF_WHEEL,
    defs.WM_MOUSEHWHEEL : defs.MOUSEEVENTF_HWHEEL,
    defs.WM_RBUTTONDOWN : defs.MOUSEEVENTF_RIGHTDOWN,
    defs.WM_RBUTTONUP : defs.MOUSEEVENTF_RIGHTUP
    }

def MouseHookFunction(self, ncode, wparam, lparam):
    if ncode != 0:
        return

    lparam = ctypes.cast(lparam, ctypes.POINTER(ctypes.c_long))

    flags = mouseFunctions[wparam]

    dx = self.client.root.winfo_pointerx()
    dy = self.client.root.winfo_pointery()

    dwData = 0
    if flags == defs.MOUSEEVENTF_WHEEL:
        delta = lparam[2] >> 16
        if delta > 120:
            delta = 120
        elif delta < 120 and delta > 0:
            delta = -120
        dwData = delta
    command = Command('MOUSE', { 'flags' : flags,
                            'dx' : dx,
                            'dy' : dy,
                            'dwData' : dwData})
    self.client.sendCommand(command)




keybdFunctions = { defs.WM_KEYDOWN : 0,
    defs.WM_KEYUP : 0x0002
    }

def KeyboardHookFunction(self, nCode, wParam, lParam):
    lParam = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_long))
    virtKey = lParam[0]
    scanCode = lParam[1]

    if wParam == 0x0104 or wParam == 0x0105:
        return
    
    flags = keybdFunctions[wParam]

    command = Command('KEYBOARD', {'bVk' : virtKey,
                                   'bScan' : scanCode,
                                   'dwFlags' : flags})
    self.client.sendCommand(command)

class HookManager:
    def __init__(self, client):
        self.client = client
        self.mouseHook = winlib.HookFunction(MouseHookFunction, defs.WH_MOUSE_LL)
        self.mouseHook.client = client
        self.mouseHook.Hook(0)

        self.keybdHook = winlib.HookFunction(KeyboardHookFunction, defs.WH_KEYBOARD_LL)
        self.keybdHook.client = client
        self.keybdHook.Hook(0)

    def __del__(self):
        self.mouseHook.Unhook()
        self.keybdHook.Unhook()




client = ClientHandler()
hookManager = HookManager(client)

commandThread = Thread(target=client.loop)
commandThread.start()

msg = ctypes.wintypes.MSG()
ctypes.windll.user32.GetMessageA(ctypes.byref(msg), 0, 0, 0)
