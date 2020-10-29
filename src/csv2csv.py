#!/usr/bin/env python

"""
Transform a CSV file into another form, adjusting the fields displayed,
field quoting, field separators, etc.

Usage: %(PROG)s -f f1,f2,f3,... [ options ] [ infile [ outfile ] ]
    -f lists field names to dump (quote if names contain spaces)
    -o sep - alternate output field separator (default is a comma)
    -i sep - alternate input field separator (default is a comma)
    -n - don't quote fields
    -D - don't use DOS/Windows line endings
    -H - do not emit the header line
  if given, infile specifies the input CSV file
  if given, outfile specifies the output CSV file
"""

# Copyright 2011 Skip Montanaro
# Author:     Skip Montanaro
# Maintainer: skip@pobox.com
# Created:    April 2007
# Keywords:   python pymacs emacs

# This software is provided as-is, without express or implied warranty.
# Permission to use, copy, modify, distribute or sell this software, without
# fee, for any purpose and by any individual or organization, is hereby
# granted, provided that the above copyright notice and this paragraph
# appear in all copies.

import csv
import sys
import getopt
import os

PROG = os.path.split(sys.argv[0])[1]

def usage(msg=None):
    if msg is not None:
        print >> sys.stderr, msg
        print >> sys.stderr
    print >> sys.stderr, (__doc__.strip() % globals())

def main(args):
    quote_style = csv.QUOTE_ALL
    escape_char = '\\'
    insep = outsep = ','
    inputfields = []
    outputfields = []
    terminator = "\r\n"
    emitheader = True

    try:
        opts, args = getopt.getopt(args, "o:i:f:DHn")
    except getopt.GetoptError, msg:
        usage(msg)
        return 1

    for opt, arg in opts:
        if opt == "-f":
            inputfields = arg.split(",")
            outputfields.extend(inputfields)
        elif opt == "-o":
            outsep = arg
        elif opt == "-i":
            insep = arg
        elif opt == "-H":
            emitheader = False
        elif opt == "-n":
            quote_style = csv.QUOTE_NONE
        elif opt == "-D":
            terminator = "\n"

    if len(args) > 2:
        usage(sys.argv[0])

    if len(args) >= 1:
        inf = open(args[0], "rb")
    else:
        inf = sys.stdin
    if len(args) == 2:
        outf = open(args[1], "wb")
    else:
        outf = sys.stdout

    class outdialect(csv.excel):
        delimiter = outsep
        quoting = quote_style
        escapechar = escape_char
        lineterminator = terminator

    # cheap trick to get the title row for the dict reader...
    reader = csv.reader(inf, delimiter=insep)
    fields = reader.next()
    if not inputfields:
        inputfields = outputfields = fields
    reader = csv.DictReader(inf, fields, delimiter=insep)
    writer = csv.DictWriter(outf, outputfields, dialect=outdialect,
                            extrasaction='ignore')
    if emitheader:
        writer.writerow(dict(zip(outputfields, outputfields)))

    try:
        for inrow in reader:
            if fields != inputfields:
                outrow = {}
                for field in inputfields:
                    outrow[field] = inrow[field]
            else:
                outrow = inrow
            writer.writerow(outrow)
    except IOError:
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
