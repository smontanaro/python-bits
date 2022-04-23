#!/usr/bin/env python3

"""
simpleminded session save/restore based on an idea by Gerrit Holl

readline module required! (implies won't work on Windows)

mark the beginning of a session by calling mark().  Save the current
session since the last mark() call by calling save().  Load a saved
session by calling load().

load from your PYTHONSTARTUP file as

    from save_session import mark, save, load

"""

__all__ = ['mark', 'save', 'load']

try:
    import readline
except ImportError as exc:
    raise ImportError("session save/restore requires readline module") from exc

import os
import sys

# needs to match the filename the user uses!
_histfile = os.path.expanduser("~/.pyhist")

# where we save sessions
_session_file = os.path.expanduser("~/.pysession")

# mark with something valid at the interpreter but unlikely to be executed
# by the user
_marker = '((1.0+999.0j, "mark", 999.0-1.0j))'

def save():
    """save the readline history since last call to mark()"""
    end = readline.get_current_history_length() - 1
    session = []
    item = readline.get_history_item(end)
    while item != _marker:
        session.insert(0, item+"\n")
        end -= 1
        item = readline.get_history_item(end)

    with open(_session_file, 'w', encoding="utf-8") as fobj:
        fobj.write("#!/usr/bin/env python3\n")
        fobj.writelines(session)
    print("saved session to", _session_file, file=sys.stderr)

def load():
    """load the last session saved by a call to save()"""
    try:
        with open(_session_file, "r", encoding="utf-8") as fobj:
            # pylint: disable=protected-access,exec-used
            exec(compile(fobj.read(), _session_file, 'exec'),
                 sys._getframe(1).f_globals)
    # pylint: disable=bare-except
    except:
        print("Session load failed. Check for error in", _session_file,
              file=sys.stderr)
    else:
        print("loaded session from", _session_file, file=sys.stderr)

def mark():
    """mark the start of a new session to save later"""
    readline.add_history(_marker)
