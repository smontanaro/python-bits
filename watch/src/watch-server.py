#!/usr/bin/env python

from xmlrpc.server import SimpleXMLRPCServer as RPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler as RPCHandler
import socket
import sys
import getopt

from watch import collector


class Server(RPCServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def main():
    opts, _args = getopt.getopt(sys.argv[1:], "p:d", ['port=', 'debug'])
    port = 8080
    debug = False
    for opt, arg in opts:
        if opt in ['-p', '--port']:
            port = int(arg)
        elif opt in ['-d', '--debug']:
            debug = True

    server = Server(('', port), RPCHandler, False)
    c = collector.Collector(debug)
    server.register_instance(c)
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
