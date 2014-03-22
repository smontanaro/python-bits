#!/usr/bin/env python

"""
Discard all pending administrative messages for a mailing list managed by
Mailman 2.1 (dunno if it works with 2.0.x).

Usage: Pull up your admindb page, scan for any valid messages and approve
them.  When the approval process is complete, save the resulting page to
a file and feed it to this script's stdin.
"""

import sys
import urllib
import urllib2
import re

### change these to suit the list
# Address of Mailman 2.1 admin page
url = "http://localhost/mailman/admindb/my-very-own-list"
passwd = "xxxxxx"

### change this to suit the load on the machine
CHUNKSZ = 100

def dump(params):

    params["adminpw"] = passwd
    paramstr = urllib.urlencode(params)

    req = urllib2.Request(url, paramstr)
    f = urllib2.urlopen(req)
    data = f.read()
    print "discarded", len(params)-1, "items for", url.split("/")[-1]

def main():
    params = {}

    for line in sys.stdin:
        mat = re.search('''"(senderaction-[^"]+)"''', line)
        if mat is not None:
            action = urllib.unquote(mat.group(1))
            params[action] = "3"

        if len(params) >= CHUNKSZ:
            dump(params)
            params = {}
            time.sleep(1)

    if params:
        dump(params)

if __name__ == "__main__":
    main()
