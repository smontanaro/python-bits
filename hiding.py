#!/usr/bin/env python

"""
Given a list of module names on the command line, poke around in the
top level functions in the modules and identify any local names that hide
builtin names.  On Unix, one way to run it is

    for f in /usr/local/lib/python1.5/*.py ; do
        python hiding.py `basename $f .py`
    done

A more obscure way to run it that avoids multiple invocations of the script
is

    mods=`ls /usr/local/lib/python1.5/*.py | xargs -n1 basename | sed -e 's/\.py$//'`
    python hiding.py $mods
"""

import sys, __builtin__, types, traceback

_builtin_names = {}
for n in dir(__builtin__): _builtin_names[n] = 1
clash = _builtin_names.has_key

def check_object(obj, nm):
    for n in dir(obj):
        o = getattr(obj, n)
        if type(o) == types.FunctionType:
            check_function(o, nm, n)
        elif type(o) == types.ClassType:
            check_class(o, nm, n)

def check_function(func, modname, me):
    funcname = "%s.%s" % (modname, me)
    if clash(me):
        print 'function', funcname, 'hides builtin name'
    check_code(func.func_code, funcname)

def check_code(co, modname):
    hdr = "%s.%s" % (modname, co.co_name)
    for nm in co.co_varnames:
        if clash(nm):
            print "variable", "%s.%s" % (modname, nm), 'hides builtin name'
    for c in co.co_consts:
        if type(c) == types.CodeType:
            check_code(c, "%s.%s" % (modname, c.co_name))

def check_module(modname):
    if clash(modname):
        print 'module', modname, 'hides builtin name'
    try:
        mod = __import__(modname)
        check_object(mod, mod.__name__)
    except:
        apply(traceback.print_exception, sys.exc_info())

def check_class(cls, modname, me):
    clsname = "%s.%s" % (modname, me)
    if clash(me):
        print 'class', clsname, 'hides builtin name'
    check_object(cls, clsname)

mods = sys.argv[1:]
for modname in mods:
    check_module(modname)
