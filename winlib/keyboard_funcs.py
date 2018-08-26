import ctypes as c
from ctypes.wintypes import BYTE

user32 = c.windll.user32
kernel32 = c.windll.kernel32

_keyBoardState = c.ARRAY(BYTE, 256)()

def GetBit(data, n):
    return (data & ( 1 << n )) >> n

def ToAscii(virtKey, scanCode, flags):
    buff = c.create_unicode_buffer(3)
    user32.GetKeyboardState(_keyBoardState)
    user32.ToUnicodeEx(virtKey, scanCode, _keyBoardState, buff, 3, flags, GetKeyboardLayout(0))
    return buff.value

def ToAscii_LPARAM(lparam):
    return ToAscii(lparam[0], lparam[1], lparam[2])

def GetKeyState(virtkey):
    val = user32.GetKeyState(virtkey)
    return bool(val >> 8), bool(val & 0x00ff)

def GetKeyboardLayout(threadId):
    return user32.GetKeyboardLayout(threadId)

def ParseLPARAM_keybd(lparam):
    return lparam & 0x0000ffff, lparam & 0x00ff0000, bool(GetBit(lparam, 24)), bool(GetBit(lparam, 29)), bool(GetBit(lparam, 30)), bool(GetBit(lparam, 31))
