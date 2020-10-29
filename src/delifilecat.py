#!/usr/bin/env python

"""
usage: %(program)s [ -f ifiledb ] [-d ] [ -h ] [ cat1 ... ]
  -f gives an alternate ifile database name.  ~/.idata is the default.
  -d enables a small amount of debugging output.
  -h prints this message and exits.
  Any remaining arguments are assumed to be categories to delete.
  The transformed database is written to stdout.
"""

import sys
import getopt
import os

# provide enumerate if it's missing (it's new in Python 2.3)
try:
    enumerate
except NameError:
    def enumerate(l):
        return zip(range(len(l)), l)

def usage():
    print >> sys.stderr, __doc__ % globals()

def main(args):
    ifiledb = os.path.expanduser("~/.idata")
    debug = False

    try:
        opts, args = getopt.getopt(args, "f:dh")
    except getopt.GetoptError:
        usage()
        return 1

    for opt, arg in opts:
        if opt == "-f":
            ifiledb = arg
        elif opt == "-d":
            debug = True
        elif opt == "-h":
            usage()
            return 0

    lines = file(ifiledb).readlines()

    # all categories in the idata file
    cats = {}
    [cats.update({cat:[n,cat,nwords,nmsgs]}) for (n,(cat,nwords,nmsgs)) in
         enumerate(zip(lines[0].strip().split(),
                       map(int, lines[1].strip().split()),
                       map(int, lines[2].strip().split())))]

    # list of categories we want to delete
    delcats = [cats.get(cat, (-1,))[0] for cat in args]
    if -1 in delcats:
        print >> sys.stderr, "invalid category in", args
        usage()
        return 1

    i = 0
    catslist = []
    for name in lines[0].split():
        if cats[name][0] not in delcats:
            catslist.append((name, i))
            i += 1

    # map old index numbers to new numbers
    newcats = {}
    for name, n in catslist:
        newcats[cats[name][0]] = n

    if debug:
        print >> sys.stderr, "delcats:", delcats
        print >> sys.stderr, "catslist:", catslist
        print >> sys.stderr, "newcats:", newcats

    # generate list of categories on stdout
    for (name, n) in catslist:
        n, cat, nwords, nmsgs = cats[name]
        if name not in delcats:
            sys.stdout.write("%s " % cat)
    sys.stdout.write("\n")
    for (name, n) in catslist:
        n, cat, nwords, nmsgs = cats[name]
        if name not in delcats:
            sys.stdout.write("%d " % nwords)
    sys.stdout.write("\n")
    for (name, n) in catslist:
        n, cat, nwords, nmsgs = cats[name]
        if name not in delcats:
            sys.stdout.write("%d " % nmsgs)
    sys.stdout.write("\n")

    # work through the rest of the idata lines deleting items from
    # deleted categories and reemitting a line if any cat:freq pairs remain
    for line in lines[3:]:
        fields = line.strip().split(" ", 2)
        word, age, freqpairs = fields
        freqpairs = [pair.split(":") for pair in freqpairs.split()]
        freqpairs = [map(int, (cat,freq)) for (cat,freq) in freqpairs]
        freqpairs = ["%s:%s"%(newcats[cat],freq)
                         for (cat,freq) in freqpairs
                             if cat not in delcats]
        freqpairs = " ".join(freqpairs)
        if freqpairs:
            sys.stdout.write("%s %s %s \n" % (word, age, freqpairs))

if __name__ == "__main__":
    program = os.path.basename(sys.argv[0])
    sys.exit(main(sys.argv[1:]))
