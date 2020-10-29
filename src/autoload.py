"""
autoload - load common symbols automatically on demand

When a NameError is raised attempt to find the name in a couple places.
Check to see if it's a name in a list of commonly used modules.  If it's
found, import the name.  If it's not in the common names try importing it.
In either case (assuming the imports succeed), reexecute the code in the
original context.
"""

import sys, traceback, re

_common = {}
# order important - most important needs to be last - os.path is chosen over
# sys.path for example
for mod in "sys os math xmlrpclib".split():
    m = __import__(mod)
    try:
        names = m.__all__
    except AttributeError:
        names = dir(m)
    names = [n for n in names if not n.startswith("_") and n.upper() != n]
    for n in names:
        _common[n] = mod

def _exec(import_stmt, tb):
    f_locals = tb.tb_frame.f_locals
    f_globals = tb.tb_frame.f_globals
    sys.excepthook = _eh
    try:
        exec import_stmt in f_locals, f_globals
        exec tb.tb_frame.f_code in f_locals, f_globals
    finally:
        sys.excepthook = _autoload_exc
    
def _autoload_exc(ty, va, tb):
##    if ty != ImportError:
##        traceback.print_exception(ty, va, tb)
##        return
    mat = re.search("name '([^']*)' is not defined", va.args[0])
    if mat is not None:
        name = mat.group(1)
        if name in _common:
            mod = _common[name]
            print >> sys.stderr, "found", name, "in", mod, "module"
            _exec("from %s import %s" % (mod, name), tb)
        else:
            print >> sys.stderr, "autoloading", name
            _exec("import %s" % name, tb)
    else:
        traceback.print_exception(ty, va, tb)

_eh = sys.excepthook
sys.excepthook = _autoload_exc
