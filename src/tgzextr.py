#!/usr/local/bin/python

# extract and display an element from a compressed tar file
# PATH_INFO represents a path to the file being browsed. 
# the file argument, if it exists, represents the file in the archive
# to display.  If it's a directory, a listing of that level in the 
# tar file is displayed.  If not given, the entire tar file is listed in
# directory format.

# Copyright 1996, Automatrix, Inc.
# Author: Skip Montanaro - skip@automatrix.com

# Example:
#   1. View a listing of the entire Python source tree:
#       http://www.automatrix.com/~skip/python/python.tar.gz
#   2. View just the Demo subdirectory:
#       http://www.automatrix.com/~skip/python/python.tar.gz?file=Python/Demo

# To do:
#   1. Snazzier listing with title at least
#   2. Should cache listing for better performance
#   3. No file argument should just display top-level listing, not
#      listing of entire file...

import addpath
import cgi, sys, os, regex, string, mimetypes

def _write(f, s):
    try:
	f.write(s)
    except IOError:
	sys.exit(1)

def _writelines(f, s):
    try:
	f.writelines(s)
    except IOError:
	sys.exit(1)

def main():
    form = cgi.FormContentDict()

    archive = os.environ['PATH_TRANSLATED']
    try:
	path = form['file'][0]
    except KeyError:
	path = ''

    tmpdir = '/tmp/%s' % os.getpid()

    try:
	os.mkdir(tmpdir, 0755)
    except os.error:
	pass

    f = os.popen('/usr/contrib/bin/gzcat %s | tar tvf - %s' % (archive, path), 'r')


    listing = f.readlines()
    if listing:

	if listing[0][0] == 'd':
	    _write(sys.stdout,'Content-type: %s\r\n\r\n' % 'text/html')
	    _write(sys.stdout,'<html><head><title>%s</title></head><body><pre>\n' %
		   path)
	    # user asked for a directory - send back a listing
	    listing = listing[1:-1]
	    splpat = regex.symcomp('\(<f>.* \)\(<r>.*\)')
	    deeppat = regex.compile('%s/[^/]*/' % path)
	    pathinfo = os.environ['PATH_INFO']
	    super = string.join(string.split(path, '/')[:-1], '/')
	    if super:
		_write(sys.stdout,' '*32)
		_write(sys.stdout,'<a href="/cgi-bin/tgzextr%s?file=%s">&lt;Up One Level&gt;</a>\n' %
		      (pathinfo, super))
	    for line in map(string.strip, listing):
		if splpat.match(line) != -1:
		    first = splpat.group('f')
		    rest = splpat.group('r')
		    if deeppat.match(rest) != -1: continue
		    _write(sys.stdout,first[:11]+first[32:])
		    _write(sys.stdout,'<a href="/cgi-bin/tgzextr%s?file=%s">%s</a>\n' %
			  (pathinfo, rest, rest))
	else:
	    fmimetype = mimetypes.get_type(path)

	    _write(sys.stdout,'Content-type: %s\r\n\r\n' % fmimetype)
	    os.chdir(tmpdir)
	    os.system("/usr/contrib/bin/gzcat %s | tar xf - %s" % (archive, path))

	    _writelines(sys.stdout,open('%s/%s' % (tmpdir, path)).readlines())

	    os.unlink('%s/%s' % (tmpdir, path))
	    path = string.split(path)[:-1]
	    try:
		while path:
		    dirs = string.join(path)
		    os.rmdir('%s/%s', (tmpdir, dirs))
		    path = path[:-1]
		os.rmdir(tmpdir)
	    except os.error:
		pass

if __name__ == "__main__": main()
