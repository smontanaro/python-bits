import ctypes
import enum
from . import _base
from pynput._util import AbstractListener as AbstractListener
from pynput._util.win32 import INPUT as INPUT, INPUT_union as INPUT_union, KEYBDINPUT as KEYBDINPUT, KeyTranslator as KeyTranslator, ListenerMixin as ListenerMixin, MapVirtualKey as MapVirtualKey, SendInput as SendInput, SystemHook as SystemHook, VkKeyScan as VkKeyScan
from typing import Any

class KeyCode(_base.KeyCode): ...

class Key(enum.Enum):
    alt: Any
    alt_l: Any
    alt_r: Any
    alt_gr: Any
    backspace: Any
    caps_lock: Any
    cmd: Any
    cmd_l: Any
    cmd_r: Any
    ctrl: Any
    ctrl_l: Any
    ctrl_r: Any
    delete: Any
    down: Any
    end: Any
    enter: Any
    esc: Any
    f1: Any
    f2: Any
    f3: Any
    f4: Any
    f5: Any
    f6: Any
    f7: Any
    f8: Any
    f9: Any
    f10: Any
    f11: Any
    f12: Any
    f13: Any
    f14: Any
    f15: Any
    f16: Any
    f17: Any
    f18: Any
    f19: Any
    f20: Any
    f21: Any
    f22: Any
    f23: Any
    f24: Any
    home: Any
    left: Any
    page_down: Any
    page_up: Any
    right: Any
    shift: Any
    shift_l: Any
    shift_r: Any
    space: Any
    tab: Any
    up: Any
    media_play_pause: Any
    media_volume_mute: Any
    media_volume_down: Any
    media_volume_up: Any
    media_previous: Any
    media_next: Any
    insert: Any
    menu: Any
    num_lock: Any
    pause: Any
    print_screen: Any
    scroll_lock: Any

class Controller(_base.Controller):
    def __init__(self, *args, **kwargs) -> None: ...

class Listener(ListenerMixin, _base.Listener):
    class _KBDLLHOOKSTRUCT(ctypes.Structure): ...
    def __init__(self, *args, **kwargs): ...
    def canonical(self, key): ...
