def help(x):
    """display an object's __doc__ attribute if it has one"""
    try:
        print "synopsis:", _prototype(x)
        if hasattr(x, "__doc__") and x.__doc__ is not None:
            print x.__doc__
    except TypeError:
        if hasattr(x, "__doc__") and x.__doc__ is not None:
            print x.__doc__
        else:
            print "no docstring available"

# from .../Include/compile.h
_OPTIMIZED = 1
_NEWLOCALS = 2
_VARARGS = 4
_VARKEYWORDS = 8

def _prototype(x):
    import types
    if type(x) not in (types.FunctionType, types.LambdaType,
                       types.MethodType, types.UnboundMethodType):
        raise TypeError, "not a function type"
    if type(x) in (types.LambdaType, types.FunctionType):
        func = x
    elif type(x) in (types.MethodType, types.UnboundMethodType):
        func = x.im_func
    code = func.func_code
    varargs = code.co_flags & _VARARGS
    varkwds = code.co_flags & _VARKEYWORDS
    args = list(code.co_varnames)
    nargs = code.co_argcount

    # decorate parameters with defaults
    dvals = list(func.func_defaults)
    i = nargs-1
    while dvals and i >= 0:
        args[i] = "%s=%s" % (args[i], `dvals.pop()`)
        i = i - 1

    # decorate varargs and varkeywords
    if varargs:
        args[nargs] = "*" + args[nargs]
        nargs = nargs + 1
    if varkwds:
        args[nargs] = "**" + args[nargs]
        nargs = nargs + 1
    
    proto = ["%s(" % code.co_name]
    proto.append(", ".join(args[:nargs]))
    proto.append(")")
    return "".join(proto)
