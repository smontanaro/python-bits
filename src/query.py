#!/usr/local/bin/python

import sys
import re
import os
import pwd
import cgi
import socket

def main():
    print 'Content-type: text/html; charset=utf-8\n\n'

    print '<h2>Environment</h2>'
    print '<table cellpadding="1" cellspacing="1">'
    keys = os.environ.keys()
    keys.sort()
    for env in keys:
	print '<tr>'
        print '<th align="left">', env, '</th>'
        print '<td>', (os.environ[env] or "&lt;EMPTY&gt;"), '</td>'
        print '</tr>'
    print "</table>"
    print ''

    form = cgi.FieldStorage()
    print '<h2>Form Fields</h2>'
    if len(form) == 0:
        print "<p>No form fields given."
    else:
        print '<table cellpadding="1" cellspacing="1">'
        keys = form.keys()
        keys.sort()
        for var in keys:
            print '<tr>'
            print '<th align="left">', var, '</th>'
            print '<td>',
            x = form[var]
            if isinstance(type(x), list):
                x = map(getattr, x, ["value"]*len(x))
                print ", ".join(x),
            elif x.file:
                print "(filename: %s, length: %d)" % (x.filename, len(x.value)),
            else:
                x, punt, encoding = decode(x.value)
                if isinstance(x, unicode):
                    x = x.encode("utf-8")
                print x, "(encoding: %s)"% encoding
            print '</td>'
            print '</tr>'
        print '</table>'

    print '<h2>Compiled-in Python Modules</h2>'
    modules = list(sys.builtin_module_names)
    modules.sort()
    print '<p>'
    for i in range(0, len(modules), 8):
	print '   ', ", ".join(modules[i:i+8])
    print '</p>'

    print '<h2>Modules Currently Loaded</h2>'
    modules = sys.modules.keys()
    modules.sort()
    print '<p>'
    print ", ".join(modules)
    print '</p>'

    print '<h2>User Information</h2>'
    print '<table cellpadding="1" cellspacing="1">'
    print '<tr>'
    print '<th align="left">User ID</th>',
    print '<td>', os.getuid(), '</td>'
    print '</tr>'
    print '<tr>'
    print '<th align="left">Group ID</th>',
    print '<td>', os.getgid(), '</td>'
    print '</tr>'
    print '<tr>'
    print '<th align="left">Effective User ID</th>',
    print '<td>', os.geteuid(), '</td>'
    print '</tr>'
    print '<tr>'
    print '<th align="left">Effective Group ID</th>',
    print '<td>', os.getegid(), '</td>'
    print '</tr>'
    print '</table>'

    print '<h2>Machine Information</h2>'
    print '<table cellpadding="1" cellspacing="1">'
    print '<tr>'
    print '<th align="left">True Hostname</th>',
    print '<td>', socket.gethostbyaddr(socket.gethostbyname(socket.gethostname())), '</td>'
    print '<tr>'
    print '<th align="left">Virtual Hostname</th>',
    print '<td>', socket.gethostbyaddr(socket.gethostbyname(os.environ['SERVER_NAME'])), '</td>'
    print '</tr>'
    print '</table>'
    
def decode(s, enc=None, denc=sys.getdefaultencoding()):
    """try interpreting s using several possible encodings.
    return value is a three-element tuple.  The first element is either an
    ASCII string or a Unicode object.  The second element is 1
    if the decoder had to punt and delete some characters from the input
    to successfully generate a Unicode object."""
    if isinstance(s, unicode):
        return s, 0, "utf-8"
    try:
        x = unicode(s, "ascii")
        # if it's ascii, we're done
        return s, 0, "ascii"
    except UnicodeError:
        encodings = ["utf-8","iso-8859-1","cp1252","iso-8859-15"]
        # if the default encoding is not ascii it's a good thing to try
        if denc != "ascii": encodings.insert(0, denc)
        # always try any caller-provided encoding first
        if enc: encodings.insert(0, enc)
        for enc in encodings:

            # Most of the characters between 0x80 and 0x9F are displayable
            # in cp1252 but are control characters in iso-8859-1.  Skip
            # iso-8859-1 if they are found, even though the unicode() call
            # might well succeed.

            if (enc in ("iso-8859-15", "iso-8859-1") and
                re.search(r"[\x80-\x9f]", s) is not None):
                continue

            # Characters in the given range are more likely to be 
            # symbols used in iso-8859-15, so even though unicode()
            # may accept such strings with those encodings, skip them.

            if (enc in ("iso-8859-1", "cp1252") and
                re.search(r"[\xa4\xa6\xa8\xb4\xb8\xbc-\xbe]", s) is not None):
                continue

            try:
                x = unicode(s, enc)
            except UnicodeError:
                pass
            else:
                if x.encode(enc) == s:
                    return x, 0, enc

        # nothing worked perfectly - try again, but use the "ignore" parameter
        # and return the longest result
        output = [(unicode(s, enc, "ignore"), enc) for enc in encodings]
        output = [(len(x), x) for x in output]
        output.sort()
        x, enc = output[-1][1]
        return x, 1, enc

if __name__ == '__main__':
    main()
