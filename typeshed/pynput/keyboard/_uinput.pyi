import enum
from . import _base
from pynput._util import xorg_keysyms as xorg_keysyms
from pynput._util.uinput import ListenerMixin as ListenerMixin
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

class Layout:
    KEYCODE_RE: Any
    class Key:
        def __init__(self, normal, shifted, alt, alt_shifted) -> None: ...
        def __iter__(self): ...
        def __getitem__(self, i): ...
        @property
        def normal(self): ...
        @property
        def shifted(self): ...
        @property
        def alt(self): ...
        @property
        def alt_shifted(self): ...
    def __init__(self): ...
    def for_vk(self, vk, modifiers): ...
    def for_char(self, char): ...

class Controller(_base.Controller):
    def __init__(self, *args, **kwargs) -> None: ...
    def __del__(self) -> None: ...

class Listener(ListenerMixin, _base.Listener):
    def __init__(self, *args, **kwargs) -> None: ...

LAYOUT: Any
