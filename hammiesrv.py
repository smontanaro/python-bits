#! /usr/bin/env python

# A server version of hammie.py


"""Usage: %(program)s [options] IP:PORT

Where:
    -h
        show usage and exit

    IP
        IP address to bind (use 0.0.0.0 to listen on all IPs of this machine)
    PORT
        Port number to listen to.
"""

import sys
import os
import getopt
import socket
    
import StringIO
from spambayes import hammie
from spambayes import Options
from spambayes import PickleRPC

try:
    True, False
except NameError:
    # Maintain compatibility with Python 2.2
    True, False = (1==1), (1==0)


program = sys.argv[0] # For usage(); referenced by docstring above

class HammieFilter(object):
    def __init__(self):
        options = Options.options
        options.mergefiles(['/etc/hammierc',
                            os.path.expanduser('~/.hammierc')])
        self.dbname = options.hammiefilter_persistent_storage_file
        self.dbname = os.path.expanduser(self.dbname)
        self.usedb = options.hammiefilter_persistent_use_database
        self.ham = hammie.open(self.dbname, self.usedb, 'r')

    def score(self, *args, **kwds):
        return self.ham.filter(args[0])


def usage(code, msg=''):
    """Print usage message and sys.exit(code)."""
    if msg:
        print >> sys.stderr, msg
        print >> sys.stderr
    print >> sys.stderr, __doc__ % globals()
    sys.exit(code)


class Server(PickleRPC.PickleRPCServer):
    def __init__(self, addr, handler=PickleRPC.PickleRPCHandler):
        PickleRPC.PickleRPCServer.__init__(self, addr, handler)
        self.h = HammieFilter()
        self.register(self.h.score)     # registers "score"
        self.register(self.methods, "system.methods")
        self.register(self.echo, "system.echo")

    def methods(self):
        return self._dispatch.keys()
    
    def echo(self, arg):
        return arg
    
def main():
    """Main program; parse options and go."""
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h')
    except getopt.error, msg:
        usage(2, msg)

    for opt, arg in opts:
        if opt == '-h':
            usage(0)

    if len(args) != 1:
        usage(2, "IP:PORT not specified")

    ip, port = args[0].split(":")
    port = int(port)

    server = Server((ip, port))
    server.serve_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
