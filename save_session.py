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
except ImportError:
    raise ImportError, "session save/restore requires readline module"

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
        
    file(_session_file, 'w').writelines(session)
    print >> sys.stderr, "saved session to", _session_file

def load():
    """load the last session saved by a call to save()"""
    try:
        execfile(_session_file, sys._getframe(1).f_globals)
    except:
        print >> sys.stderr, ("Session load failed. Check for error in %s" %
                              _session_file)
    else:
        print >> sys.stderr, "loaded session from", _session_file

def mark():
    """mark the start of a new session to save later"""
    readline.add_history(_marker)
