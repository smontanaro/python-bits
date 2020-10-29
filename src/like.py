#!/usr/bin/env python3

import sys
import os
import glob
import grp

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

def main(args):
    results = set()
    for directory in os.environ.get("PATH", "").split(":"):
        for prog in args:
            for path in glob.glob(os.path.join(directory, "*%s*" % prog)):
                if executable(path):
                    results.add(path)
    # Check for shell functions.
    for line in os.popen("bash -ci 'declare -F'"):
        func = line.strip().split()[-1]
        for prog in args:
            if prog in func:
                results.add(func)
    results = list(results)
    results.sort()

    for prog in results:
        print(prog)

if __name__ == "__main__":
    main(sys.argv[1:])
