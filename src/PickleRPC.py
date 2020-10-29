
"""
RPC using pickles as the serialization mechanism over raw sockets

WARNING: This module uses pickles without any consideration of the security
implications.  Before considering this code for *anything other than toy
applications* please be sure you read and understand the security
implications of using the pickle module.  In particular, read this
document carefully:

    http://www.python.org/doc/current/lib/pickle-sec.html

Security Update: The PickleRPCHandler and Proxy classes now use an instance
of the Unpickler class to unpickle data.  It restricts unpickling of
instances to classes in the exceptions module.  Users who want to play with
passing other types of data back and forth can subclass PickleRPCHandler and
Proxy classes and provide a different unpickler.
"""

import SocketServer
import socket
import sys
import traceback
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
try:
    import cPickle as pickle
except ImportError:
    print >> sys.stderr, "Only cPickle is supported"
    raise

__all__ = ["Error", "PickleRPCServer", "PickleRPCHandler", "Proxy"]

_debug = 0

class Error(Exception):
    pass

class PickleRPCServer(SocketServer.TCPServer):
    allow_reuse_address = 1
    def __init__(self, *args):
        SocketServer.TCPServer.__init__(self, *args)
        self._dispatch = {}

    def register(self, func, name=None):
        self._dispatch[name or func.__name__] = func

    def _call(self, method, args, kwds):
        return self._dispatch[method](*args, **kwds)

class Unpickler:
    def loads(self, data):
        s = StringIO.StringIO(data)
        up = pickle.Unpickler(s)
        up.find_global = self.find_global
        return up.load()
    
    def find_global(self, module, name):
        if module != "exceptions":
            raise pickle.UnpicklingError, (module, name)
        mod = __import__(module)
        return getattr(mod, name)

class PickleRPCHandler(SocketServer.StreamRequestHandler):
    def __init__(self, *args):
        self.unpickler = Unpickler()
        SocketServer.StreamRequestHandler.__init__(self, *args)

    def handle(self):
        nbytes = int(self.rfile.read(7), 16)
        if _debug > 0: print "receiving", nbytes, "bytes"
        data = ""
        while nbytes:
            new = self.rfile.read(nbytes)
            nbytes -= len(new)
            data += new
        try:
            (method, args, kwds) = self.unpickler.loads(data)
        except pickle.UnpicklingError, msg:
            result = None
            ty, va, tb = sys.exc_info()
            tbtext = "".join(traceback.format_exception(ty, va, tb))
            exceptinfo = (ty, va, tbtext)
        else:
            try:
                result = self.server._call(method, args, kwds)
                exceptinfo = None
            except:
                result = None
                ty, va, tb = sys.exc_info()
                tbtext = "".join(traceback.format_exception(ty, va, tb))
                exceptinfo = (ty, va, tbtext)
        data = pickle.dumps((result, exceptinfo))
        nbytes = "%07x" % len(data)
        if _debug > 0: print "sending", nbytes, "bytes"
        self.wfile.write(nbytes)
        self.wfile.write(data)
        self.wfile.flush()
        self.connection.shutdown(1)

class Proxy:
    def __init__(self, address):
        self.address = address
        self.unpickler = Unpickler()

    def __getattr__(self, name):
        return _Method(self._request, name)

    def _request(self, method, *args, **kwds):
        packet = pickle.dumps((method, args, kwds))
        nbytes = "%07x" % len(packet)
        if _debug > 0: print "sending", nbytes, "bytes"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.address)
        s.send(nbytes)
        s.send(packet)
        nbytes = int(s.recv(7), 16)
        data = ""
        while nbytes:
            new = s.recv(nbytes)
            nbytes -= len(new)
            data += new
        s.close()
        if _debug > 0: print "received", len(data), "bytes"
        try:
            result, exceptinfo = self.unpickler.loads(data)
        except pickle.UnpicklingError:
            raise Error, "invalid data"
        if exceptinfo is not None:
            raise Error, exceptinfo
        else:
            return result

# snagged from xmlrpclib
class _Method:
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args, **kwds):
        return self.__send(self.__name, *args, **kwds)
