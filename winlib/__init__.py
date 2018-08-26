import ctypes as c
from ctypes.wintypes import *

user32 = c.windll.user32
kernel32 = c.windll.kernel32

DLL_FAIL_LOAD = 0x1
DLL_FAIL_FUNCTION = 0x2

class winlib_DLLFail():

    def __init__(self, dllname, funcname, code):
        self.code = code
        self.dllname = dllname
        self.funcname = funcname
    def getErrorCode(self):
        return self.code
    def getErrorMessage(self):
        if self.code == DLL_FAIL_LOAD:
            print("DLL<" + self.dllname + "> Failed to load. It either could not be found or is corrupt.")
        else:
            print("Function<" + self.funcname + "> is not a valid function in the dll <" + self.dllname + ">.")
            
class winlib_Window():
    def __init__(self, handle):
        self.handle = handle

    @property
    def title(self):
        length = user32.GetWindowTextLengthW(self.handle)
        buff = c.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(self.handle, buff, length + 1)
        return buff.value

    def getChildren(self):
        arr = []
        def _enumProc(hwnd, lparam):
            win = winlib_Window(hwnd)
            arr.append(win)
        functype = c.WINFUNCTYPE(c.c_bool, c.POINTER(c.c_int), c.POINTER(c.c_int))
        user32.EnumChildWindows(self.handle, functype(_enumProc), 0)
        return arr

    def getHandle(self):
        p = c.cast(c.byref(self.handle), c.POINTER(c.c_long))
        return p.contents.value

    def __iter__(self):
        self._currentChildren = self.getChildren()
        self._childrenSize = len(self._currentChildren)
        self._childIndex = 0
        return self

    def __next__(self):
        if self._childIndex >= self._childrenSize:
            raise StopIteration
        else:
            r = self._currentChildren[self._childIndex]
            self._childIndex += 1
            return r

    def CallWindowFuncStr(self, name, *params, dll="user32", strfunc=False):
        handle = c.cdll.LoadLibrary(dll)
        print(params)
        if strfunc:
            name += "W"
        func = handle.__getattr__(name)
        func(self.handle, *params)

    def getThreadId(self):
        return user32.GetWindowThreadProcessId(self.handle, None)
    
    def __str__(self):
        return "winlib.winlib_Window object: HWND(" + str(self.getHandle()) + "), TITLE(\"" + self.title + "\")"

class HookFunction:
    def __init__(self, func, idHook):
        self.idHook = idHook
        self.func = func

    def Hook(self, dwThreadId):
        self.c_func = GetHookFuncPointer(self.__hookProc)
        self.hook = SetThreadHook_Raw(self.idHook, self.c_func, dwThreadId)

    def Unhook(self):
        if self.hook == -1: return
        user32.UnhookWindowsHookEx(self.hook)
        self.hook = -1
    
    def __hookProc(self, ncode, wparam, lparam):
        self.func(self, ncode, wparam, lparam)
        return user32.CallNextHookEx(self.hook, ncode, wparam, lparam)
    
def SetThreadHook_Raw(idHook : int, func, dwThreadId):
    return user32.SetWindowsHookExA(idHook, func, kernel32.GetModuleHandleW(None), dwThreadId)

def GetHookFuncPointer(func):
    type = c.CFUNCTYPE(c.c_int, c.c_int, c.c_int, c.POINTER(c.c_void_p))
    return type(func)

def GetFunc_DLL(funcname, dll="user32"):
    
    d = None
    try:
        d = c.cdll.LoadLibrary(dll)
    except OSError:
        return winlib_DLLFail(dll, funcname, DLL_FAIL_LOAD)

    try:
        return d.__getattr__(funcname)
    except AttributeError:
        try:
            return d.__getattr__(funcname + "W")
        except AttributeError:
            return winlib_DLLFail(dll, funcname, DLL_FAIL_FUNCTION)

def CallFunc_DLL(funcname, *params, dll="user32"):

    d = None
    try:
        d = c.cdll.LoadLibrary(dll)
    except OSError:
        return winlib_DLLFail(dll, funcname, DLL_FAIL_LOAD)

    try:
        return d.__getattr__(funcname)(*params)
    except AttributeError:
        try:
            return d.__getattr__(funcname + "W")(*params)
        except AttributeError:
            return winlib_DLLFail(dll, funcname, DLL_FAIL_FUNCTION)

def SearchWindows(name : str):
    potentials = []
    def _enumProc(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = c.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)

            if name.lower().replace(" ", "") in buff.value.lower().replace(" ", ""):
                potentials.append(winlib_Window(hwnd))
        return True

    ftype = c.WINFUNCTYPE(c.c_bool, c.POINTER(c.c_int), c.POINTER(c.c_int))
    user32.EnumWindows(ftype(_enumProc), 0)
    
    if len(potentials) > 1:
        return tuple(potentials)
    elif len(potentials) == 1:
        return potentials[0]
    else:
        return None

def GetCurrentThreadId():
    return kernel32.GetCurrentThreadId()
