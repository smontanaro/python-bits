#!/usr/local/bin/python

import whrandom, string, socket, SOCKET, time

def get_data(conn):
    try:
	stuff = []
	stuff.append(conn.recv(1024))
	while 1:
	    data = conn.recv(1024)
	    if not data: break
	    stuff.append(data)
	return string.join(stuff, '')
    except socket.error:
	conn.close()
	return ''

def send_receive(data, ctype, connectargs):
    s = socket.socket(ctype, SOCKET.SOCK_STREAM)
    try:
	apply(s.connect, connectargs)
    except socket.error:
	return None

    if s.send(data) != len(data):
	return None

    s.shutdown(1)

    return get_data(s)

#make string of 100 random printable characters to shoot to server...
stuff = []
for i in range(60):
    stuff.append(chr(int(32+whrandom.random()*64)))
stuff = string.join(stuff, '')
print stuff

lengths = [50, 100, 200, 500, 1000, 2000, 5000]

for n in lengths:
    t = time.time()
    i = 0
    while i < n:
	result = send_receive(stuff, SOCKET.AF_INET, ('', 5101))
	i = i + 1
    print 'inet (%d)' % n, (time.time()-t)

    t = time.time()
    i = 0
    while i < n:
	result = send_receive(stuff, SOCKET.AF_UNIX, ('5101',))
	i = i + 1
    print 'unix (%d)' % n, (time.time()-t)
