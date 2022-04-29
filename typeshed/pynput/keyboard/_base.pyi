import enum
from collections.abc import Generator
from pynput._util import AbstractListener as AbstractListener, prefix as prefix
from typing import Any

class KeyCode:
    vk: Any
    char: Any
    is_dead: Any
    combining: Any
    def __init__(self, vk: Any | None = ..., char: Any | None = ..., is_dead: bool = ..., **kwargs) -> None: ...
    def __eq__(self, other): ...
    def __hash__(self): ...
    def join(self, key): ...
    @classmethod
    def from_vk(cls, vk, **kwargs): ...
    @classmethod
    def from_char(cls, char, **kwargs): ...
    @classmethod
    def from_dead(cls, char, **kwargs): ...

class Key(enum.Enum):
    alt: int
    alt_l: int
    alt_r: int
    alt_gr: int
    backspace: int
    caps_lock: int
    cmd: int
    cmd_l: int
    cmd_r: int
    ctrl: int
    ctrl_l: int
    ctrl_r: int
    delete: int
    down: int
    end: int
    enter: int
    esc: int
    f1: int
    f2: int
    f3: int
    f4: int
    f5: int
    f6: int
    f7: int
    f8: int
    f9: int
    f10: int
    f11: int
    f12: int
    f13: int
    f14: int
    f15: int
    f16: int
    f17: int
    f18: int
    f19: int
    f20: int
    home: int
    left: int
    page_down: int
    page_up: int
    right: int
    shift: int
    shift_l: int
    shift_r: int
    space: int
    tab: int
    up: int
    media_play_pause: int
    media_volume_mute: int
    media_volume_down: int
    media_volume_up: int
    media_previous: int
    media_next: int
    insert: int
    menu: int
    num_lock: int
    pause: int
    print_screen: int
    scroll_lock: int

class Controller:
    class InvalidKeyException(Exception): ...
    class InvalidCharacterException(Exception): ...
    def __init__(self) -> None: ...
    def press(self, key) -> None: ...
    def release(self, key) -> None: ...
    def tap(self, key) -> None: ...
    def touch(self, key, is_press) -> None: ...
    def pressed(self, *args) -> Generator[None, None, None]: ...
    def type(self, string) -> None: ...
    @property
    def modifiers(self) -> Generator[Any, None, None]: ...
    @property
    def alt_pressed(self): ...
    @property
    def alt_gr_pressed(self): ...
    @property
    def ctrl_pressed(self): ...
    @property
    def shift_pressed(self): ...

class Listener(AbstractListener):
    def __init__(self, on_press: Any | None = ..., on_release: Any | None = ..., suppress: bool = ..., **kwargs) -> None: ...
    def canonical(self, key): ...
