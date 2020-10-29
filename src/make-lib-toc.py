#!/usr/local/bin/python1.5
#	-*- python -*-

import httplib, sys, time, os, re, string, stat

libsource = '/doc/lib/lib.html'
tocfile = os.path.expanduser('~skip/public_html/python/libtoc.html')
def get_lib_toc():
    if os.path.exists(tocfile):
	timestamp = os.stat(tocfile)[stat.ST_MTIME]
    else:
	timestamp = 0

    httpobj = httplib.HTTP('www.python.org', 80)
    httpobj.putrequest('GET', libsource)
    httpobj.putheader('If-Modified-Since', time.strftime('%a, %d %b %Y %X GMT',
							 time.localtime(timestamp)))
    httpobj.putheader('Accept', 'text/html')
    httpobj.endheaders()

    reply, msg, hdrs = httpobj.getreply()
    if reply == 200:
	return httpobj.getfile().readlines()
    else:
	return []

def compare(s,t):
    s = string.lower(s[0][0])
    t = string.lower(t[0][0])
    if s < t: return -1
    if s > t: return 1
    return 0

def main():
    mpat = re.compile(' *HREF="([^"]*)">'
                      '<SPAN[^>]*>[0-9]+</SPAN>\.<SPAN[^>]*>[0-9]+</SPAN>'
                      ' +<tt>([^<]*)</tt> --',
                      re.I)

    lines = get_lib_toc()
    if lines:
	modules = []
	for line in lines:
	    m = mpat.match(string.strip(line))
	    if m is not None:
		modules.append(map(string.strip, map(m.group, [2, 1])))

	if not modules:
	    print "Error! No lines in the library manual matched!"
	    return

	out = open(tocfile, 'w')
	out.write("""
	<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 3.0//EN">
	<HTML>
	<HEAD>
	<TITLE>Python Library Module Quick Reference</TITLE>
	<base href="http://www.python.org%s"
	</HEAD>
	<BODY bgcolor="white">
	<H1 ALIGN=CENTER>Python v1.5 Library Module Quick Reference</H1>

	<p>Extracted from the
	<a href="lib.html">Python Library Reference Manual</a>.

	<p>Updated: %s
	<p>
	<table border=1 width="100%%">
	""" % (libsource, time.strftime('%a, %d %b %Y %X GMT',
					time.localtime(time.time()))))

	modules.sort(compare)
	ldict = {}
	for ent in modules:
	    # make key lower case so _ sorts ahead of letters later on
	    first = string.lower(ent[0][0])
	    try:
		ldict[first].append(ent)
	    except KeyError:
		ldict[first] = [ent]

	# split into two groups, one set for the first column and one
	# for the right
	# this is very crude - but my brain is a little fried from lack
	# of sleep, so I'm doing it the brute force way
	half = len(ldict)/2+len(ldict)%2
	keys = ldict.keys()
	keys.sort()
	left = keys[:half]
	right = keys[half:]
	    
	ncols = 3
	for i in range(len(left)):
	    out.write("<tr>\n")

	    # left hand column
	    letter = ldict[left[i]]
	    out.write("<th>%s\n" % string.upper(left[i]))
	    out.write("<td>\n")
	    out.write("<table>\n")
	    col = 0
	    for ent in letter:
		if col == 0:
		    out.write("<tr>\n")

		col = (col + 1) % ncols
		out.write('<td><a href="%s">%s</a></td>\n' %
			  (ent[1], ent[0]))
	    out.write("</table>\n")

	    # try to emit a right-hand column
	    try:
		letter = ldict[right[i]]
		out.write("<th>%s\n" % string.upper(right[i]))
		out.write("<td>\n")
		out.write("<table>\n")
		col = 0
		for ent in letter:
		    if col == 0:
			out.write("<tr>\n")

		    col = (col + 1) % ncols
		    out.write('<td><a href="%s">%s</a></td>\n' %
			      (ent[1], ent[0]))
		out.write("</table>\n")
	    except IndexError:
		out.write("<td colspan=2>&nbsp;\n")

	out.write("""
	</table>
	<p>Last Modified: %s
	</body>
	</html>
	""" % (time.strftime('%a, %d %b %Y %X GMT', time.localtime(time.time()))))

if __name__ == '__main__':
    main()
