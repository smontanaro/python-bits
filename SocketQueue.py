
"""Queue implemented using sockets.

In one shell, execute:

    python SocketQueue.py server

then in another shell, execute

    python SocketQueue.py client

Implementation of non-blocking behavior is left as an exercise for the
reader. <wink>
"""

import socket
import cPickle as pickle

class SocketQueueServer:
    def __init__(self, address):
        self.sock = socket.socket()
        self.sock.bind(address)
        self.sock.listen(1)
        self.conn, remote = self.sock.accept()
        print "connection from", remote
        self.f = self.conn.makefile("rb")

    def get(self):
        return pickle.load(self.f)

    def close(self):
        self.f.close()
        self.sock.close()

class SocketQueueClient:
    def __init__(self, address):
        self.sock = socket.socket()
        self.sock.connect(address)
        self.f = self.sock.makefile("wb")

    def put(self, obj):
        pickle.dump(obj, self.f)

    def close(self):
        self.f.close()
        self.sock.close()

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "server":
        queue = SocketQueueServer(('', 4050))
        for i in range(10):
            print queue.get()
        queue.close()

    else:
        queue = SocketQueueClient(('', 4050))
        for i in range(10):
            queue.put(i)
        queue.close()
