from . import _base
from pynput._util.xorg import ListenerMixin as ListenerMixin, display_manager as display_manager
from typing import Any

Button: Any

class Controller(_base.Controller):
    def __init__(self, *args, **kwargs) -> None: ...
    def __del__(self) -> None: ...

class Listener(ListenerMixin, _base.Listener):
    def __init__(self, *args, **kwargs) -> None: ...
