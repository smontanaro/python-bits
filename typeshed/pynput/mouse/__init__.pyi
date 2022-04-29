from pynput._util import Events as _Events, backend as backend
from typing import Any

Button: Any
Controller: Any
Listener: Any

class Events(_Events):
    class Move(_Events.Event):
        x: Any
        y: Any
        def __init__(self, x, y) -> None: ...
    class Click(_Events.Event):
        x: Any
        y: Any
        button: Any
        pressed: Any
        def __init__(self, x, y, button, pressed) -> None: ...
    class Scroll(_Events.Event):
        x: Any
        y: Any
        dx: Any
        dy: Any
        def __init__(self, x, y, dx, dy) -> None: ...
    def __init__(self) -> None: ...
