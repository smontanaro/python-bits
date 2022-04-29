import enum
from . import _base
from pynput._util import NotifierMixin as NotifierMixin
from pynput._util.xorg import ListenerMixin as ListenerMixin, alt_gr_mask as alt_gr_mask, alt_mask as alt_mask, char_to_keysym as char_to_keysym, display_manager as display_manager, index_to_shift as index_to_shift, keyboard_mapping as keyboard_mapping, numlock_mask as numlock_mask, shift_to_index as shift_to_index, symbol_to_keysym as symbol_to_keysym
from pynput._util.xorg_keysyms import CHARS as CHARS, DEAD_KEYS as DEAD_KEYS, KEYPAD_KEYS as KEYPAD_KEYS, KEYSYMS as KEYSYMS, SYMBOLS as SYMBOLS
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

class Controller(NotifierMixin, _base.Controller):
    CTRL_MASK: Any
    SHIFT_MASK: Any
    ALT_MASK: Any
    ALT_GR_MASK: Any
    def __init__(self, *args, **kwargs) -> None: ...
    def __del__(self) -> None: ...
    @property
    def keyboard_mapping(self): ...

class Listener(ListenerMixin, _base.Listener):
    def __init__(self, *args, **kwargs) -> None: ...
