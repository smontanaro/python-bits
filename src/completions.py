try:
    import rlcompleter
except ImportError:
    pass
else:
    try:
        import readline
    except ImportError:
        pass
    else:
        readline.parse_and_bind("tab: complete")
        try:
            readline.read_history_file
        except AttributeError:
            pass
        else:
            import os
            histfile = os.path.join(os.environ["HOME"], ".pyhist")
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            import atexit
            atexit.register(readline.write_history_file, histfile)
            del os, histfile
