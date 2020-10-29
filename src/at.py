#!/usr/bin/python

import sys
import datetime
import tempfile
import os

import dateutil.parser

now = datetime.datetime.now()

args = " ".join(sys.argv[1:])
dt = dateutil.parser.parse(args)

days = (dt-now).days
hhmm = dt.strftime("%H:%M")
if days < 0:
    print >> sys.stderr, "timespec in the past:", dt
    sys.exit(1)
if days == 0:
    timespec = hhmm
else:
    timespec = "%s + %d day" % (hhmm, days)

fname = tempfile.mktemp()
f = open(fname, 'w')
while True:
    sys.stdout.write("at> ")
    sys.stdout.flush()
    line = sys.stdin.readline()
    if line.strip() == "." or not line:
        print "done"
        break
    f.write(line)
f.write("rm %s\n" % fname)
f.close()
os.system("at -f %s %s < /dev/null" % (fname, timespec))
