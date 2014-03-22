
"""
The alarms module provides an alarm capability for applications that use
asyncore.  Instead of using a static timeout in the event loop, if the time
until the next alarm is shorter than the regular timeout, that value is used
as the timeout for the poll function.  Whenever an alarm expires, the
handle_alarm method is called.  It can be overridden to 

To use this code, mixin the AsyncAlarmMixin class (or more likely, a
subclass of it) into your asyncore.dispatcher subclass.  Then, make calls to
the set_alarm or set_relative_alarm methods to add new alarms as desired.
Make sure to call the loop method defined here instead of asyncore.loop.

Override handle_alarm in your subclass to define application-specific
alarm handling behavior.
"""

import asyncore
import time

class AsyncAlarmMixin:
    def __init__(self):
        self.alarms = []

    def set_alarm(self, t, data=None):
        """set an alarm for time t (expressed in seconds since the epoch).

        'data' is an arbitrary object which will be passed to handle_alarm.

        if you override this method, make sure you chain up to this one,
        otherwise your alarm will not be saved."""
        #print "setting alarm for %.5f @ %.5f" % (t, time.time())
        self.alarms.append((t, data))
        self.alarms.sort()

    def set_relative_alarm(self, t, data=None):
        """set an alarm for t seconds from now.

        'data' is an arbitrary object which will be passed to handle_alarm.

        if you override this, make sure you call this, otherwise
        your alarm will not be saved."""
        self.set_alarm(time.time()+t, data)

    def handle_alarm(self, data):
        """respond to an alarm - generally overridden in a subclass"""
        print "alarm @ %.5f with data %s handled @ %.5f" % \
              (self.alarms[0][0], self.alarms[0][1], time.time())

    def loop (self, timeout=30.0, use_poll=0, map=None):
        """alternate event loop for asyncore apps that handles alarms"""
        if map is None:
            map=asyncore.socket_map

        if use_poll:
            if hasattr (select, 'poll'):
                poll_fun = asyncore.poll3
            else:
                poll_fun = asyncore.poll2
        else:
            poll_fun = asyncore.poll

        while map:
            while self.alarms and time.time() >= self.alarms[0][0]:
                self.handle_alarm(self.alarms[0][1])
                del self.alarms[0]
            t = timeout
            if self.alarms:
                t = min(timeout, max(self.alarms[0][0]-time.time(), 0.01))
            poll_fun (t, map)

if __name__ == "__main__":
    import time
    import socket

    class http_client(AsyncAlarmMixin,asyncore.dispatcher):
        def __init__(self, host,path):
            asyncore.dispatcher.__init__(self)
            AsyncAlarmMixin.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect( (host, 80) )
            self.set_relative_alarm(1.5)
            self.set_alarm(time.time()+1)
            self.set_relative_alarm(0.5)
            self.buffer = 'GET %s HTTP/1.0\r\n' % path
            self.buffer += 'Host: %s\r\n' % host
            self.buffer += '\r\n'

        def handle_connect(self):
            pass

        def handle_read(self):
            data = self.recv(8192)
            if data:
                print len(data)

        def writable(self):
            return self.buffer

        def handle_write(self):
            sent = self.send(self.buffer)
            self.buffer = self.buffer[sent:]

        def handle_close(self):
            if not self.alarms:
                self.close()

    http = http_client("www.musi-cal.com",
                       "/search?city=New+York,NY&radius=20")
    http.loop()
