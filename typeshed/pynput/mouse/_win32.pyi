import ctypes
import enum
from . import _base
from pynput._util import NotifierMixin as NotifierMixin
from pynput._util.win32 import INPUT as INPUT, INPUT_union as INPUT_union, ListenerMixin as ListenerMixin, MOUSEINPUT as MOUSEINPUT, SendInput as SendInput, SystemHook as SystemHook
from typing import Any

WHEEL_DELTA: int

class Button(enum.Enum):
    unknown: Any
    left: Any
    middle: Any
    right: Any
    x1: Any
    x2: Any

class Controller(NotifierMixin, _base.Controller):
    def __init__(self, *args, **kwargs) -> None: ...

class Listener(ListenerMixin, _base.Listener):
    WM_LBUTTONDOWN: int
    WM_LBUTTONUP: int
    WM_MBUTTONDOWN: int
    WM_MBUTTONUP: int
    WM_MOUSEMOVE: int
    WM_MOUSEWHEEL: int
    WM_MOUSEHWHEEL: int
    WM_RBUTTONDOWN: int
    WM_RBUTTONUP: int
    WM_XBUTTONDOWN: int
    WM_XBUTTONUP: int
    MK_XBUTTON1: int
    MK_XBUTTON2: int
    XBUTTON1: int
    XBUTTON2: int
    CLICK_BUTTONS: Any
    X_BUTTONS: Any
    SCROLL_BUTTONS: Any
    class _MSLLHOOKSTRUCT(ctypes.Structure): ...
    def __init__(self, *args, **kwargs): ...
