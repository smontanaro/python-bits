import ctypes
from . import AbstractListener as AbstractListener
from typing import Any

class MOUSEINPUT(ctypes.Structure):
    MOVE: int
    LEFTDOWN: int
    LEFTUP: int
    RIGHTDOWN: int
    RIGHTUP: int
    MIDDLEDOWN: int
    MIDDLEUP: int
    XDOWN: int
    XUP: int
    WHEEL: int
    HWHEEL: int
    ABSOLUTE: int
    XBUTTON1: int
    XBUTTON2: int

class KEYBDINPUT(ctypes.Structure):
    EXTENDEDKEY: int
    KEYUP: int
    SCANCODE: int
    UNICODE: int

class HARDWAREINPUT(ctypes.Structure): ...
class INPUT_union(ctypes.Union): ...

class INPUT(ctypes.Structure):
    MOUSE: int
    KEYBOARD: int
    HARDWARE: int

LPINPUT: Any
VkKeyScan: Any
MapVirtualKey: Any
SendInput: Any
GetCurrentThreadId: Any

class MessageLoop:
    WM_STOP: int
    PM_NOREMOVE: int
    thread: Any
    def __init__(self) -> None: ...
    def __iter__(self): ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def post(self, msg, wparam, lparam) -> None: ...

class SystemHook:
    HC_ACTION: int
    class SuppressException(Exception): ...
    hook_id: Any
    on_hook: Any
    def __init__(self, hook_id, on_hook=...) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type, value, traceback) -> None: ...

class ListenerMixin:
    def suppress_event(self) -> None: ...

class KeyTranslator:
    def __init__(self) -> None: ...
    def __call__(self, vk, is_press): ...
    def update_layout(self) -> None: ...
    def char_from_scan(self, scan): ...
