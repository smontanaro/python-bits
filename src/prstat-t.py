#!/usr/bin/env python

"""
prstat wrapper intended for use in logging contexts.

usage: (prstat-t [ prstat args ] >> /some/log/file </dev/null &) &
"""

# Copyright 2009 - Skip Montanaro
# This program has been placed in the public domain.

# prstat is pretty much a top replacement, however it fails to emit a
# timestamp with each update and is generally intended to be used
# interactively.  This wrapper adds a timestamp for each chunk of
# output emitted by prstat.

# source: http://svnhost:3690/svn/people/skipm/trunk/scripts/prstat-t.py

import os
import sys
import datetime
from subprocess import Popen, PIPE

def main(args):
    if "-h" in args:
        print >> sys.stderr, __doc__.strip()
        return 0

    os.environ["TERM"] = "dumb"
    cmd = "prstat -c %s" % " ".join(args)
    pipe = Popen(cmd, shell=True, bufsize=1, stdout=PIPE).stdout
    lines = []

    while True:
        while True:
            line = pipe.readline()
            if not lines:
                now = datetime.datetime.now()
                lines.append("\n%79s\n" % now.strftime("%H:%M:%S"))
            lines.append(line.replace("\015", ""))
            if "Total:" in line:
                sys.stdout.writelines(lines)
                sys.stdout.flush()
                lines[:] = []

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        pass
