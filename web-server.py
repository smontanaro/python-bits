#!/usr/bin/env python

"""

This is an *experimental* threaded web server, really nothing more than a
lark at this point, based upon the CGIHTTPServer module.  A couple people
asked about it, so here it is.  Feel free to hack around with it.  Support
is neither offered nor implied.  (Hey, you get what you pay for! ;-) Still,
if you have comments, questions, find bugs, extend it or figure out neato
ways to do things I did in a clumsy fashion, feel free to pass it along.  I
can't commit to fixing it, but it might serve as a useful example for
others.

Since I was just experimenting on my development machine, I made one
modification directly to the BaseHTTPServer module.  I made the HTTPServer
class there a subclass of SocketServer.ThreadingTCPServer instead of
SocketServer.TCPServer:

    class HTTPServer(SocketServer.ThreadingTCPServer):
        ...

The thread that is spawned to handle each request simply calls the
appropriate function, once it figures out what that function is.

URLs take the following form:

    http://servername:8100/module?args

You can change the port number in the run() function at the end of this
file.  The server attempts to import the module then call

    module.cgimain(env, stdin, stdout)

Make sure your cgimain function and the things it calls don't rely on the
module globals os.environ, sys.stdin or sys.stdout, because they are almost
certainly guaranteed to not be what you want.  Also, since it's called in a
multi-threaded environment, don't write to any module-level globals without
acquiring a lock first!

Comment out the import addpath and os.chdir lines below.  The CGI script I
was converting figures out what database it's accessing based upon its
current directory, and the addpath module extends sys.path to point at
directories with local modules.  Probably not the best arrangements, but
they work.

Redirections are handled by defining the redirect_re_list class variable
below.  Again, that stuff is the way it is (particularly hard-coding the
server name and port) because I was just fooling around looking for the
quickest way to get something running.  Each element is a two-element tuple.
The first slot is an re compiled regex.  The second slot is a template whose
\\1, \\2, etc fields are substituted from the match by a call to re.sub.

Is it faster?  Hard to say at this point.  It certainly seems to consume
less system memory.  From reading the Linux thread FAQ, it seems that the
clone() and fork() call times are about the same, so the only startup
overhead saved is probably imports and memory copies.

"""

import string, urllib, thread, os, sys, re, time
import CGIHTTPServer, BaseHTTPServer

# comment these out!
import addpath
os.chdir('/usr/local/Automatrix/concerts')

class PythonCGIRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):
    """
    Overrides CGI processing to handle in thread instead of forking.
    """

    redirect_re_list = [
	(re.compile("(/icons/.*)"),
	 "http://concerts.calendar.com\\1"),
	(re.compile("/cgi-bin/event-search(.*)"),
	 "http://dolphin.automatrix.com:8100/esearch/ConcertServerInfo\\1"),
	(re.compile("/cgi-bin/simple-search(?:/ConcertServerInfo)?\?key=([^&]*)&value=(.*)"),
	 "http://dolphin.automatrix.com:8100/esearch/ConcertServerInfo?\\1=\\2"),
	(re.compile("/concerts(/.*)"),
	 "http://concerts.calendar.com\\1"),
	]

    def is_redirect(self):
	for r, t in self.redirect_re_list:
	    m = r.match(self.path)
	    if m is not None:
		return re.sub(r, t, self.path)
	return None

    def is_cgi(self):
	# separate module and path info from args
	path = string.split(self.path[1:], '?')
	if len(path) == 1:
	    self._args = ""
	else:
	    self._args = path[1]
	module = path[0]

	# separate module from path_info
        i = string.find(module, '/')
        if i >= 0:
	    self._module, self._path_info = module[:i], module[i:]
        else:
            self._module, self._path_info = module, ''

	# if we can import the module and it defines cgimain, we're golden
	__import__(self._module)
	module = sys.modules[self._module]
	mainfunc = getattr(module, 'cgimain')
	self.cgi_info = ("/", string.join(path, '?'))
	return 1

    def do_GET(self):
	url = self.is_redirect()
	if url is not None:
	    self.do_redirect(url)
        elif self.is_cgi():
            self.run_cgi()
        else:
            self.send_error(404, "Script not found")

    def do_redirect(self, url):
        self.send_response(302, "Moved")
        self.send_header("Content-type", "text/html")
	self.send_header("Location", url)
        self.end_headers()
	self.wfile.write('''
	<p> Document moved to <a href="%s">%s</a>.
	''' % (url, url))

    def run_cgi(self):
        """
	Set up and run the appropriate function in this thread (don't fork).

	The path to the script can be

	    /module/path?args
    
        where module is an importable module that defines a function
	named 'cgimain' that takes three arguments, a dictionary
	corresponding to os.environ, stdin, and stdout for the thread.
	The path and args have their normal CGI interpretations.
	"""
        self.send_response(200, "Script output follows")
        self.wfile.flush()
        try:
            # Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
            # XXX Much of the following could be prepared ahead of time!
            env = {}
            env['SERVER_SOFTWARE'] = self.version_string()
            env['SERVER_NAME'] = self.server.server_name
            env['GATEWAY_INTERFACE'] = 'CGI/1.1'
            env['SERVER_PROTOCOL'] = self.protocol_version
            env['SERVER_PORT'] = str(self.server.server_port)
            env['REQUEST_METHOD'] = self.command
            env['PATH_INFO'] = urllib.unquote(self._path_info)
            env['PATH_TRANSLATED'] = self.translate_path(env['PATH_INFO'])
            env['SCRIPT_NAME'] = "/%s" % self._module
            if self._args: env['QUERY_STRING'] = self._args
            host = self.address_string()
            if host != self.client_address[0]:
                env['REMOTE_HOST'] = host
            env['REMOTE_ADDR'] = self.client_address[0]
            # AUTH_TYPE
            # REMOTE_USER
            # REMOTE_IDENT
            env['CONTENT_TYPE'] = self.headers.type
            length = self.headers.getheader('content-length')
            if length:
                env['CONTENT_LENGTH'] = length
            accept = []
            for line in self.headers.getallmatchingheaders('accept'):
                if line[:1] in string.whitespace:
                    accept.append(string.strip(line))
                else:
                    accept = accept + string.split(line[7:])
            env['HTTP_ACCEPT'] = string.joinfields(accept, ',')
            ua = self.headers.getheader('user-agent')
            if ua:
                env['HTTP_USER_AGENT'] = ua
            # XXX Other HTTP_* headers
	    func = getattr(sys.modules[self._module], 'cgimain')
	    func(env, self.rfile, self.wfile)
        except:
            self.server.handle_error(self.request, self.client_address)
            os._exit(127)

def print_bases(cls, indent=""):
    if not indent:
	print
	print "HTTPServer inheritance:"
	print "%s.%s" % (cls.__module__, cls.__name__)
    indent = indent + "  "
    for b in cls.__bases__:
	print indent, "%s.%s" % (b.__module__, b.__name__)
	print_bases(b, indent)

def run(server_class=BaseHTTPServer.HTTPServer,
	handler_class=PythonCGIRequestHandler):
    server_address = ('', 8100)
    print_bases(server_class)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == "__main__": run()
