#!/usr/bin/env python

"""
The DXPServer allows people to store and retrieve dynamic instruction
frequency information for Python programs.  It is hoped that by offering
this service to the Python community a large database of instruction count
frequencies can be accumulated for different versions of Python.

The DXPserver currently implements just a few methods:

    add_dx_info(appname, email, pyversion, dxlist)
        Register the dynamic instruction frequencies for a single
        application run by a particular email address, using a particular
        version of Python.  There is no real useful return value unless
        an error is detected.

        appname: A non-empty string that identifies the application that
        generated this instruction profile.

        email: A valid email address (while this is logged, it will only be
        used to contact the owner of a misbehaving client).

        pyversion: A three-element tuple as returned by
        sys.version_info[:3].  People running pre-2.0 versions of Python
        will have to synthesize this from the first word of sys.version.
        All three elements must be ints.
          
        dxlist: A run-length encoded version of the list returned by
        sys.getdxp().  You will only have this function available if you
        compiled your Python interpreter with the DYNAMIC_EXECUTION_PROFILE
        macro defined.  You can choose to define DXPAIRS as well or not.
        This method accepts either type of getdxp() output.  The run-length
        encoding is described below.

    get_dx_info(pyversion)

        Return the instruction profiling information that has been
        accumulated for version pyversion.  The format for pyversion is the
        same as in add_dx_info.  The return value is a dictionary with two
        keys: 'counts' and 'pairs'.  The value associated with the 'counts'
        key is a run-length encoded list of opcode frequencies as would be
        returned by rle(sys.getdxp()) without DXPAIRS defined.  The value
        associated with the 'pairs' key is a list of opcode frequencies as
        would be returned by rle(sys.getdxp()) with DXPAIRS defined.  If
        there is no information recorded for one category or another
        appropriate zero-filled lists are returned.

    versions()
        Return the version numbers for which this server has some
        instruction counts.

    usage()
        Return detailed usage information.

    synopsis()
        Return brief usage information.

The input dxlist and the output returned by get_dx_info must be run-length
encoded.  The algorithm is straightforward:

    def rle(l):
        newl = []
        lastel = None
        count = 0
        for elt in l:
            if elt == lastel:
                count = count + 1
                continue
            elif lastel is not None:
                if isinstance(lastel, types.ListType):
                    lastel = rle(lastel)
                newl.append([lastel, count])
            lastel = elt
            count = 1
        if isinstance(lastel, types.ListType):
            lastel = rle(lastel)
        newl.append([lastel, count])
        return newl

Use the following to run-length encode sys.getdxp() output:

    dxinfo = rle(sys.getdxp())

Decoding is similar:

    def rld(l):
        newl = []
        for elt, count in l:
            if isinstance(elt, types.ListType):
                elt = rld(elt)
            newl.extend([elt]*count)
        return newl

    dxinfo = rld(rpcserver.get_dx_info((1,5,2)))

Both rle() and rld() are included in the dxpserver.py module/script
available from <http://www.musi-cal.com/~skip/python/>.

You can use the atexit module to automatically transmit instruction counts
to the server at normal program termination:

    def send_instruction_counts(appname, email):
        if not hasattr(sys, 'getdxp'):
            return
        dxpserver = xmlrpclib.Server('http://manatee.mojam.com:7304')
        dxpserver.add_dx_info(appname, email, sys.version_info[:3],
                              rle(sys.getdxp()))

    import atexit
    atexit.register(send_instruction_counts, 'myapp', 'me@some.where')
"""

import sys
import types
import os
import getopt
import shelve
from SimpleXMLRPCServer import SimpleXMLRPCServer as RPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler as RPCHandler

if os.path.exists("/Users/skip"):
    DXPAIRDB = "/Users/skip/misc/dxpair.db"
else:
    DXPAIRDB = "/home/skip/misc/dxpair.db"

class DB:
    def __init__(self, file):
        self.db = shelve.open(file)

    def get(self, key, default=None):
        if self.db.has_key(key):
            return self.db[key]
        else:
            return default

    def __getattr__(self, attr):
        return getattr(self.db, attr)

    def __del__(self):
        self.db.close()

class DXPServer(RPCServer):
    def __init__(self, address):
        RPCServer.__init__(self, address, RPCHandler, False)

    def server_bind(self):
        import socket
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.bind(self.server_address)

class DXPMethods:
    """Methods to collect dynamic execution info"""
    def __init__(self, dxpairdb):
        self.dxpairdb = dxpairdb

    def synopsis(self, *args):
        """\
usage:

    dxp.add_dx_info(appname, author, pyversion, dxlist)

    dxp.get_dx_info(pyversion)

    dxp.synopsis()
        
    dxp.usage()

    dxp.versions()
    
For detailed instructions, execute the server's usage() method.
"""
        return DXPMethods.synopsis.__doc__
    
    def usage(self, *args):
        return __doc__

    def add_dx_info(self, appname=None, email=None, pyversion=None,
                    dxlist=None):
        if not email or not isinstance(email, types.StringType):
            return ("Error: missing or invalid email.\n\n"+
                    self.synopsis())

        if not (pyversion and
                isinstance(pyversion, types.ListType) and
                len(pyversion) == 3 and
                map(type, pyversion) == [types.IntType]*3):
            return ("Error: missing or invalid version info.\n\n"+
                    self.synopsis())

        if not appname or not isinstance(appname, types.StringType):
            return ("Error: missing or invalid application name.\n\n"+
                    self.synopsis())

        pyversion = tuple(pyversion)

        db = DB(self.dxpairdb)
        emails = db.get("emails", {})
        thisemail = emails[email] = emails.get(email, {})
        if not thisemail.get("__valid", 1):
            return 'thanks'

        thisemail[appname] = thisemail.get(appname, 0) + 1
        db["emails"] = emails

        dxinfoversion = "dxinfo.%d.%d.%d" % pyversion

        dxlist = rld(dxlist)
        
        dxinfo = db.get(dxinfoversion)
        if dxinfo is None:
            dxinfo = [0] * 256
        else:
            dxinfo = rld(dxinfo)

        if len(dxlist) == 257:
            dxcounts = dxlist[256]
        else:
            dxcounts = dxlist
        for i in range(256):
            dxinfo[i] = dxinfo[i] + dxcounts[i]
        db[dxinfoversion] = rle(dxinfo)

        if len(dxlist) == 257:
            dxpairversion = "dxpair.%d.%d.%d" % pyversion
            dxpairinfo = db.get(dxpairversion)
            if dxpairinfo is None:
                dxpairinfo = []
                for i in range(256):
                    dxpairinfo.append([0]*256)
            else:
                dxpairinfo = rld(dxpairinfo)
            for i in range(256):
                for j in range(256):
                    dxpairinfo[i][j] = dxpairinfo[i][j] + dxlist[i][j]
            db[dxpairversion] = rle(dxpairinfo)

        db.close()

        return 'thanks'
    
    def get_dx_info(self, pyversion=None):
        if not (pyversion and
                isinstance(pyversion, types.ListType) and
                len(pyversion) == 3 and
                map(type, pyversion) == [types.IntType]*3):
            return ("Error: missing or invalid version info.\n\n"+
                    self.synopsis())

        pyversion = tuple(pyversion)
        
        dxinfoversion = "dxinfo.%d.%d.%d" % pyversion
        dxpairversion = "dxpair.%d.%d.%d" % pyversion

        db = DB(self.dxpairdb)
        dxinfo = db.get(dxinfoversion)
        dxpairinfo = db.get(dxpairversion)
        db.close()

        if dxinfo is None:
            dxinfo = rle([0]*256)

        if dxpairinfo is None:
            dxpairinfo = []
            for i in range(256):
                dxpairinfo.append([0]*256)
            dxpairinfo = rle(dxpairinfo)

        return {"counts": dxinfo, "pairs": dxpairinfo}

    def versions(self):
        db = DB(self.dxpairdb)
        keys = db.keys()
        v = []
        for key in keys:
            if key[:6] == "dxinfo":
                v.append(map(int, key.split(".")[1:]))
        return v
        
    def invalidate_email(self, email):
        db = DB(self.dxpairdb)
        emails = db.get("emails", {})
        thisemail = emails[email] = emails.get(email, {})
        thisemail["__valid"] = 0
        db["emails"] = emails
        return 0

    def _dispatch(self, method, params):
        if hasattr(self, method):
            return getattr(self, method)(*params)
        else:
            return ("Error: unrecognized method: %s.\n\n"%method+
                    self.synopsis())

def rle(l):
    newl = []
    lastel = None
    count = 0
    for elt in l:
        if elt == lastel:
            count = count + 1
            continue
        elif lastel is not None:
            if isinstance(lastel, types.ListType):
                lastel = rle(lastel)
            newl.append([lastel, count])
        lastel = elt
        count = 1
    if isinstance(lastel, types.ListType):
        lastel = rle(lastel)
    newl.append([lastel, count])
    return newl

def rld(l):
    newl = []
    for elt, count in l:
        if isinstance(elt, types.ListType):
            elt = rld(elt)
        newl.extend([elt]*count)
    return newl

def main():
    dxpairdb = DXPAIRDB
    opts, args = getopt.getopt(sys.argv[1:], "d:")
    for opt, arg in opts:
        if opt == "-d":
            dxpairdb = arg

    dbserver = DXPServer(("", 7304))
    dbserver.register_instance(DXPMethods(dxpairdb))

    try:
        dbserver.serve_forever()
    except KeyboardInterrupt:
        raise SystemExit

    return

if __name__ == "__main__":
    main()
