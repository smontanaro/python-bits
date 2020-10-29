#!/usr/bin/env python

"""
Rebinding reload() function.

The implementation is very simpleminded at this point.  Only Python
functions, new-style and classic classes and instance methods defined at the
top level of the reloaded module are tracked during reload, and only top
level attributes of other modules are rebound.

"""

import sys
import types

def super_reload(mod, rebind_types=(types.FunctionType, # python functions
                                    types.ClassType, # classic classes
                                    types.MethodType, # instance methods
                                    types.TypeType, # new-style classes
                                    )):
    assert type(mod) == type(sys)
    ids = {}
    d = mod.__dict__
    for key in d:
        if type(d[key]) in rebind_types:
            ids[id(d[key])] = key
    newmod = reload(mod)
    rebind_globals(ids, newmod)
    return newmod

def rebind_globals(ids, newmod):
    """Rebind module attributes whose id() appear in ids.

    Only considers top-level attributes in modules.
    """

    for name in sys.modules:
        if sys.modules[name] == newmod:
            continue
        m = sys.modules[name]
        for key in dir(m):
            oldid = id(getattr(m, key))
            if oldid in ids:
                attr = getattr(newmod, ids[oldid])
                setattr(m, key, attr)

if __name__ == "__main__":
    import unittest

    class TestCase(unittest.TestCase):
        def test_ext(self):
            exc_info = sys.exc_info
            mod = super_reload(sys)
            self.assertEqual(exc_info, sys.exc_info)

        def test_py_function(self):
            global _obj
            import urllib
            _obj = obj = urllib.quote
            mod = super_reload(urllib)
            self.assertEqual(_obj, urllib.quote)
            self.assertNotEqual(obj, urllib.quote)

        def test_classic_class(self):
            global _obj
            import urllib
            _obj = obj = urllib.URLopener
            mod = super_reload(urllib)
            self.assertNotEqual(_obj, obj)
            self.assertEqual(_obj, urllib.URLopener)

        def test_new_class(self):
            global _obj
            import _strptime
            _obj = obj = _strptime.LocaleTime
            mod = super_reload(_strptime)
            self.assertEqual(_obj, _strptime.LocaleTime)
            self.assertNotEqual(obj, _strptime.LocaleTime)

    unittest.main()
