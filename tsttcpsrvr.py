#!/usr/local/bin/python

import socket, SOCKET, sockmisc, select, os

unix_sock = '/tmp/socket.tst'

s_inet = socket.socket(SOCKET.AF_INET, SOCKET.SOCK_STREAM)
s_unix = socket.socket(SOCKET.AF_UNIX, SOCKET.SOCK_STREAM)

s_inet.setsockopt(SOCKET.SOL_SOCKET, SOCKET.SO_REUSEADDR, 1)
s_inet.bind('', 5101)
s_inet.listen(512)

try:
    os.unlink(unix_sock)
except:
    pass

s_unix.setsockopt(SOCKET.SOL_SOCKET, SOCKET.SO_REUSEADDR, 1)
s_unix.bind(unix_sock)
s_unix.listen(512)

while 1:
    fds = select.select([s_unix, s_inet], [], [])
    conn, addr = fds[0][0].accept()
    data = conn.recv(100)
    result = data * 10
    bytes = conn.send(result)
    conn.close()
