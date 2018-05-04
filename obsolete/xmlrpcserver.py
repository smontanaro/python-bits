#!/usr/bin/env python
# simple xml-rpc validation server
# author: Skip Montanaro (skip@mojam.com)
# date 2000-06-05

import sys, exceptions, traceback, types, os, SocketServer, re, threading
import string, time, xmlrpclib, BaseHTTPServer, socket, select, signal

try:
    import zlib
except ImportError:
    zlib = None

def _tb():
    info = sys.exc_info()
    tb = traceback.extract_tb(info[2])
    msg = []
    for (file, line, func, text) in tb:
        msg.append('    %s:%d in %s\n        %s\n' %
                   (file, line, func, text))
    msg.append("%s: %s\n" % (info[0], info[1]))
    msg = string.join(msg, "")
    del info
    return msg
    
class Server(SocketServer.TCPServer):
    """generic XML-RPC server class"""

    def __init__(self, server_address, RequestHandlerClass):
        # how do I get the server to exit cleanly so an immediate restart
        # doesn't yield "address already in use"?
        while 1:
            try:
                SocketServer.TCPServer.__init__(self, server_address,
                                                RequestHandlerClass)
            except socket.error, info:
                if info[0] == 98:
                    time.sleep(1.0)
                    continue
                raise
            break
	self.socket.setblocking(0)
	self.me = socket.gethostbyaddr(socket.gethostbyname(socket.gethostname()))[0]
	self.port = server_address[1]
        
        self.dispatch = {
            'noop': self.noop,
            'echo': self.echo,
	    'methods': self.get_methods,
            'exit': self.exit,
            'validator1.arrayOfStructsTest': self.arrayOfStructsTest,
            'validator1.countTheEntities': self.countTheEntities,
            'validator1.easyStructTest': self.easyStructTest,
            'validator1.echoStructTest': self.echoStructTest,
            'validator1.manyTypesTest': self.manyTypesTest,
            'validator1.moderateSizeArrayCheck': self.moderateSizeArrayCheck,
            'validator1.nestedStructTest': self.nestedStructTest,
            'validator1.simpleStructReturnTest': self.simpleStructReturnTest,
            }

        self.serving = 1

    ### XML-RPC Validation test methods
        
    def arrayOfStructsTest(self, a):
        ncurlies = 0
        for s in a:
            ncurlies = ncurlies + s.get("curly", 0)
        return ncurlies

    def countTheEntities(self, s):
        return {'ctLeftAngleBrackets': string.count(s, "<"),
                'ctRightAngleBrackets': string.count(s, ">"),
                'ctAmpersands': string.count(s, "&"),
                'ctApostrophes': string.count(s, "'"),
                'ctQuotes': string.count(s, '"')}
        
    def easyStructTest(self, s):
        return (s.get("moe", 0)
                + s.get("larry", 0)
                + s.get("curly", 0))

    def echoStructTest(self, s):
        return s

    def manyTypesTest(self, num,bool,s,doub,dateTime,base64):
        return [num, bool, s, doub, dateTime,base64]

    def moderateSizeArrayCheck(self, array):
        return array[0] + array[-1]

    def nestedStructTest(self, s):
        s = s['2000']['04']['01']
        return (s.get("moe", 0)
                + s.get("larry", 0)
                + s.get("curly", 0))

    def simpleStructReturnTest(self, number):
        return {'times10': number * 10,
                'times100': number * 100,
                'times1000': number * 1000}
    
    ### non-validator methods
    
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.socket.bind(self.server_address)

    def get_methods(self):
	m = self.dispatch.keys()
	m.sort
	return m

    def exit(self):
        self.serving = 0
        return 0
    
    def noop(self):
        """nil operation"""
        return "noop"

    def echo(self, *args):
        """echo args back to client - for testing network & encode/decode time"""
        return args

    def serve_forever(self):
        nreq = 0
        while self.serving:
            nreq = nreq + 1
	    try:
		r,w,e = select.select([self.socket], [], [], 5)
		if r:
                    self.handle_request()
	    except xmlrpclib.ProtocolError:
		excinfo = apply(traceback.format_exception, sys.exc_info())
		excinfo = string.join(excinfo, "")

    def get_request(self):
	return SocketServer.TCPServer.get_request(self)

class XMLRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request,
                                                       client_address, server)

    xmlrpclib_version = "xmlrpclib/" + xmlrpclib.__version__

    def version_string(self):
	return (BaseHTTPServer.BaseHTTPRequestHandler.version_string(self)
		+ " " + self.xmlrpclib_version)

    def setup(self):
	self.connection = self.request
	self.connection.setblocking(1)
	self.rfile = self.connection.makefile('rb', 2**15)
	self.wfile = self.connection.makefile('wb', 2**15)
    
    def finish(self):
	self.connection.setblocking(0)
	#return BaseHTTPServer.BaseHTTPRequestHandler.finish(self)

    def address_string(self):
        """don't look up client hostname, just log IP address"""
        return self.client_address[0]

    def bad_request(self, code, msg):
        response = xmlrpclib.dumps(xmlrpclib.Fault(code, msg),
                                   methodresponse=1
                                   )
        self.send_response(code)
        self.send_header("Content-type", "text/xml")
        self.send_header("Content-length", "%d" % len(response))
        self.end_headers()

	self.wfile.write(response)
        self.wfile.flush()
        self.connection.shutdown(1)

    def traceback(self):
        msg = _tb()
        sys.stderr.write("error:\n%s\n" % msg)
        self.bad_request(200, msg)

    def do_POST(self):
        try:
            length = int(self.headers["content-length"])
        except KeyError:
            self.bad_request(411, "Length Required")
            return
        
        try:
            content_type = self.headers["content-type"]
            if string.strip(string.split(content_type, ";")[0]) != "text/xml":
                self.bad_request(415,
                                 "Incorrect Media Type: %s" % content_type)
                return
            
        except KeyError:
            self.bad_request(415, "No Media Type")
            return
        
        try:
            accept_encoding = self.headers["accept-encoding"]
            if accept_encoding:
                accept_encoding = map(string.strip,
                                      string.split(accept_encoding, ","))
            else:
                accept_encoding = []
        except KeyError:
            accept_encoding = []        
        
        data = self.rfile.read(length)
	left = length - len(data)
	while left:
	    data = data + self.rfile.read(left)
	    left = length - len(data)

	params, method = xmlrpclib.loads(data)

        # generate response
        try:
            response = self.call(method, params)
        except:
            # report exception back to server
            self.traceback()
            return
        else:
            response = xmlrpclib.dumps((response,), methodresponse=1)
            
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        # if we can generate gzipped encodings and the client can accept
        # them and the response is fairly long, zip it up...
        if (zlib is not None and
            "gzip" in accept_encoding and
            len(response) > 1000):
            self.send_header("Content-encoding", "x-gzip")
            response = zlib.compress(response)
        self.send_header("Content-length", "%d" % len(response))
        self.end_headers()

        i = 0
        while i < len(response):
            self.wfile.write(response[i:i+1024])
            self.wfile.flush()
            i = i + 1024

    def send_header(self, keyword, value):
	return BaseHTTPServer.BaseHTTPRequestHandler.send_header(self,
								 keyword,
								 value)

    # skip logging HTTP requests
    def log_message(self, format, *args):
        pass

    def call(self, method, params):
        try:
            meth = self.server.dispatch[method]
        except KeyError:
            raise xmlrpclib.Fault(2, "%s: unrecognized method: '%s'" %
				  (self.server.me, method))
        except:
            raise xmlrpclib.Fault(3, "%s: uncaught exception: '%s'" %
				  (self.server.me,
				   _tb(self.server.method(),
				       self.server.params())))
        try:
            return apply(meth, params)
        except:
            self.traceback()

if __name__ == "__main__":
    server = Server(('', 8000), XMLRequestHandler)
    server.serve_forever()
