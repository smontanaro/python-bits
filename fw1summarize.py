#!/usr/bin/env python

# Copyright 2003, Northwestern University.
# All rights reserved.

# $Revision: 1.9 $
# $Date: 2003/05/29 20:20:56 $

"""
This script prints a brief summary of a Firewall-1 log file to stdout.

usage: python %(prog)s [ options ] logfile

where logfile is a logfile dumped with

    fw logexport -d ';'

Options:

-h         - Print this usage and exit.
-N         - Don't perform hostname lookups on IP addresses.
-n num     - Display this many items in the tables (default top 10).
-m         - stdin is a mail message, format output as a mail message
-r rules   - csv rules file produced by Volker Tanger's fw1rules package, for
             example:

              export FW1R=/usr/local/src/fw1rules-7.3.29
              alias fw1rules=$FW1R/fw1rules.pl'
              cd /var/opt/CPfw1-50/conf
              fw1rules --output=rules.csv --template=$FW1R/templates/rules.csv

             The default is a file named 'rules.csv' in the current
             directory.
-f col=val - Only consider records where column 'col' has value 'val'.
             If multiple -f flags are given all must match for a record
             to be considered.  Column names must be taken from this set:

              num, date, time, orig, type, action, alert, i/f_name, 
              i/f_dir, product, src, s_port, dst, service, proto, 
              rule, th_flags, message_info, icmp-type, icmp-code, 
              sys_msgs, cp_message, sys_message

             'val' can be a comma-separated list of values.  a cell matches
             any of them it's considered to match.  For example, you could
             give '-f action=drop,reject' to filter all rows where the
             action column was 'drop' or 'reject'.

It has only been tested with Firewall-1 NG FP2.  Experience with other
versions of Firewall-1 is welcome.  Please send feedback to the author, Skip
Montanaro (skip@pobox.com).
"""

import os
import sys
import socket
import getopt
import time
import operator
import getpass

prog = os.path.split(sys.argv[0])[1]

def usage(msg=None):
    if msg is not None:
        print >> sys.stderr, msg
    print >> sys.stderr, __doc__ % globals()

try:
    import csv

    class fw1dialect(csv.Dialect):
        lineterminator = '\n'
        escapechar = '\\'
        skipinitialspace = False
        quotechar = '"'
        quoting = csv.QUOTE_ALL
        delimiter = ';'
        doublequote = True

    csv.register_dialect("fw1", fw1dialect)
except ImportError, AttributeError:
    usage("A recent version of the Python csv module (new in 2.3) is required.")
    sys.exit(1)
    
def mapaddr(addr, cache):
    try:
        return cache[addr]
    except KeyError:
        pass
    try:
        info = socket.gethostbyaddr(addr)
    except (socket.error):
        info = (addr, [], [addr])
    cache[addr] = info[0]
    return cache[addr]

def print_section(tagline, f1width, fieldnames, values):
    print
    print "%s:" % tagline
    print "%*s\t%6s\t%5s" % ((f1width,) + fieldnames)
    print "%*s\t%6s\t%5s" % (f1width, "-"*f1width, "-----", "-----")
    for count, name, percent in values:
        print "%*s\t%6d\t%5.2f" % (f1width, name, count, percent)

def main(args):
    mapips = True
    mailinout = False
    rulefile = "rules.csv"
    topn = 10
    filters = []

    try:
        opts, args = getopt.getopt(args, "hNmr:n:f:")
    except getopt.error, msg:
        usage(msg)
        return 1

    for opt, arg in opts:
        if opt == "-N":
            mapips = False
        elif opt == "-m":
            mailinout = True
        elif opt == "-n":
            topn = int(arg)
        elif opt == "-r":
            rulefile = arg
        elif opt == "-f":
            key, val = arg.split("=", 1)
            val = tuple(val.split(","))
            filters.append((key, val))
        elif opt == "-h":
            usage()
            return 0

    if len(args) > 1:
        usage()
        return 1
    if len(args) == 0:
        f = sys.stdin
    else:
        f = open(args[0], "rb")

    if mailinout:
        # skip message header
        while True:
            line = f.readline()
            if not line.strip():
                break

    rulemap = {}
    rulefields = ("Number","From","To","Service","Action","Track",
                  "Time","Install on","Comment")
    rdr = csv.DictReader(file(rulefile),
                         fieldnames=rulefields, dialect="excel")

    for row in rdr:
        rulemap[row["Number"]] = row["Comment"]

    fieldnames = ("num;date;time;orig;type;action;alert;i/f_name;"
                  "i/f_dir;product;src;s_port;dst;service;proto;"
                  "rule;th_flags;message_info;icmp-type;icmp-code;"
                  "sys_msgs;cp_message;sys_message").split(';')
    rdr = csv.DictReader(f, fieldnames=fieldnames, dialect="fw1")

    sources = {}
    targets = {}
    services = {}
    rules = {}

    namemap = {}

    nrows = 0
    for row in rdr:
        if row["num"] is None:
            continue
        nrows += 1

        for (key,val) in filters:
            if row.get(key) not in val:
                break
        else:
            source = row.get("src") or "unknown"
            sources[source] = sources.get(source, 0) + 1

            target = row.get("dst") or "unknown"
            targets[target] = targets.get(target, 0) + 1

            service = row.get("service") or "unknown"
            services[service] = services.get(service, 0) + 1

            rule = row.get("rule") or "unknown"
            if (rule == "unknown" and
                row.get("info", "").find("th_flags") != -1):
                rule = "proto err"      # protocol error detected by FW-1
            rules[rule] = rules.get(rule, 0) + 1

    if mailinout:
        t = time.asctime()
        whoami = getpass.getuser()
        print "From", whoami, t
        print "From: %s@localhost" % whoami
        print "To: %s@localhost" % whoami
        print "Date:", t
        print "Subject: FW-1 log"
        print "Content-type: text/plain"
        print

    print "Summary of firewall activity (%d total rows)" % nrows
    
    # compute percentages, sort, trim various stuff
    nsources = 0
    for v in sources.values():
        nsources += v
    sources = [(sources[k], k, sources[k]*100.0/nsources) for k in sources]
    sources.sort()
    sources = sources[-topn:]

    ntargets = 0
    for v in targets.values():
        ntargets += v
    targets = [(targets[k], k, targets[k]*100.0/ntargets) for k in targets]
    targets.sort()
    targets = targets[-topn:]

    nservices = 0
    for v in services.values():
        nservices += v
    services = [(services[k], k, services[k]*100.0/nservices)
                  for k in services]
    services.sort()
    services = services[-topn:]

    nrules = 0
    for v in rules.values():
        nrules += v
    rules = [(rules[k], rulemap.get(k,k), rules[k]*100.0/nrules)
               for k in rules]
    rules.sort()
    rules = rules[-topn:]

    if mapips:
        sources = [(c,mapaddr(n, namemap),p) for (c,n,p) in sources]
        targets = [(c,mapaddr(n, namemap),p) for (c,n,p) in targets]

    # figure out how wide to make the first column
    width = 0
    for count, name, percent in sources:
        width = max(width, len(name))
    for count, name, percent in targets:
        width = max(width, len(name))
    for count, name, percent in services:
        width = max(width, len(name))
    for count, name, percent in rules:
        width = max(width, len(name))

    print_section("Most frequent sources", width,
                  ("source", "count", "%"), sources)
    print_section("Most frequent targets", width,
                  ("target", "count", "%"), targets)
    print_section("Most frequent services", width,
                  ("service", "count", "%"), services)
    print_section("Most frequent rules used", width,
                  ("rule", "count", "%"), rules)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
