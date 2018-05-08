#!/usr/bin/env python

import getopt
import logging
import socket
import sys

from six.moves.xmlrpc_server import SimpleXMLRPCServer as RPCServer
from six.moves.xmlrpc_server import SimpleXMLRPCRequestHandler as RPCHandler

from watch import collector


class Server(RPCServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

FORMAT = '{asctime} {levelname} {message}'

def main():
    opts, _args = getopt.getopt(sys.argv[1:], "p:d", ['port=', 'debug'])
    port = 8080
    debug = False
    for opt, arg in opts:
        if opt in ['-p', '--port']:
            port = int(arg)
        elif opt in ['-d', '--debug']:
            debug = True

    logging.basicConfig(level="DEBUG" if debug else "INFO", style='{',
                        format=FORMAT)

    server = Server(('', port), RPCHandler, False)
    c = collector.Collector()
    server.register_instance(c)
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
