#! /usr/bin/env python

"""A client for hammiesrv.

Just feed it your mail on stdin, and it spits out the same message
with the spambayes score in a new X-Spambayes-Disposition header.

"""

import sys

from spambayes import PickleRPC


def main():
    proxy = PickleRPC.Proxy(("localhost", 65000))
    print >> sys.stderr, proxy.system.methods()
    sys.stdout.write(proxy.score(sys.stdin.read()))

if __name__ == "__main__":
    main()
