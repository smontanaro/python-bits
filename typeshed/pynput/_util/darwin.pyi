from . import AbstractListener as AbstractListener
from collections.abc import Generator
from typing import Any

class CarbonExtra:
    TISCopyCurrentKeyboardInputSource: Any
    TISCopyCurrentASCIICapableKeyboardLayoutInputSource: Any
    kTISPropertyUnicodeKeyLayoutData: Any
    TISGetInputSourceProperty: Any
    LMGetKbdType: Any
    kUCKeyActionDisplay: int
    kUCKeyTranslateNoDeadKeysBit: int
    UCKeyTranslate: Any

def keycode_context() -> Generator[Any, None, None]: ...
def keycode_to_string(context, keycode, modifier_state: int = ...): ...
def get_unicode_to_keycode_map(): ...

class ListenerMixin:
    IS_TRUSTED: bool
