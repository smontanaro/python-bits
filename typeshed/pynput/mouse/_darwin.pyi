import enum
from . import _base
from pynput._util.darwin import ListenerMixin as ListenerMixin
from typing import Any

class Button(enum.Enum):
    unknown: Any
    left: Any
    middle: Any
    right: Any

class Controller(_base.Controller):
    def __init__(self, *args, **kwargs) -> None: ...
    def __enter__(self): ...
    def __exit__(self, exc_type, value, traceback) -> None: ...

class Listener(ListenerMixin, _base.Listener):
    def __init__(self, *args, **kwargs) -> None: ...
