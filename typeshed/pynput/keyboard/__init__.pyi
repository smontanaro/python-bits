from collections.abc import Generator
from pynput._util import Events as _Events, backend as backend
from typing import Any

KeyCode: Any
Key: Any
Controller: Any
Listener: Any

class Events(_Events):
    class Press(_Events.Event):
        key: Any
        def __init__(self, key) -> None: ...
    class Release(_Events.Event):
        key: Any
        def __init__(self, key) -> None: ...
    def __init__(self) -> None: ...

class HotKey:
    def __init__(self, keys, on_activate) -> None: ...
    @staticmethod
    def parse(keys) -> Generator[None, None, Any]: ...
    def press(self, key) -> None: ...
    def release(self, key) -> None: ...

class GlobalHotKeys(Listener):
    def __init__(self, hotkeys, *args, **kwargs) -> None: ...
