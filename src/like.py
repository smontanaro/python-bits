#!/usr/bin/env python3

"""===========
%(PROG)s
===========

----------------------------------------------------
Find programs matching the given string(s).
----------------------------------------------------

:Author: skip.montanaro@gmail.com
:Date: long time ago
:Copyright: Skip Montanaro 2020
:Version: 1
:Manual section: 1
:Manual group: shell helpers

SYNOPSIS
========

 %(PROG)s [-h ] pattern ...

OPTIONS
=======

-h         display help

Patterns are just simple strings.

DESCRIPTION
===========

Check PATH and defined shell functions for executable files containing
the given patterns.

EXAMPLE
=======

Find programs which convert PNM files into a different image file format::

    $ like pnmto
    /bin/pnmtoddif
    /bin/pnmtofiasco
    /bin/pnmtofits
    /bin/pnmtojbig
    /bin/pnmtojpeg
    ...

VERSION
=======

@@VERSION@@

SEE ALSO
========

* type (shell builtin)

"""

import getopt
import glob
import grp
import os
import sys

PROG = os.path.split(sys.argv[0])[1]

def executable(path):
    path = os.path.abspath(path)
    if not os.path.exists(path) or os.path.isdir(path):
        return False
    try:
        statinfo = os.stat(path)
    except OSError:
        return False
    return (
        # I own path and owner execute bit is set *or*
        statinfo.st_uid == os.geteuid() and
        statinfo.st_mode & 0o100 or
        # I am in path's group and group execute bit is set *or*
        (statinfo.st_gid == os.getegid() or
         os.environ["USER"] in grp.getgrgid(statinfo.st_gid).gr_mem) and
        statinfo.st_mode & 0o010 or
        # other execute bit is set
        statinfo.st_mode & 0o001)

def usage(msg=None):
    if msg is not None:
        print(msg, file=sys.stderr)
        print(file=sys.stderr)
    print((__doc__.strip() % globals()), file=sys.stderr)

def main(args):
    try:
        opts, args = getopt.getopt(args, "h")
    except getopt.GetoptError as msg:
        usage(msg)
        return 1

    for opt, _arg in opts:
        if opt == "-h":
            usage()
            return 0

    results = set()
    for directory in os.environ.get("PATH", "").split(":"):
        for prog in args:
            for path in glob.glob(os.path.join(directory, f"*{prog}*")):
                if executable(path):
                    results.add(path)
    # Check for shell functions.
    for line in os.popen("/bin/bash -ci 'declare -F'"): # nosec
        func = line.strip().split()[-1]
        for prog in args:
            if prog in func:
                results.add(func)
    results = list(results)
    results.sort()

    for prog in results:
        print(prog)

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
