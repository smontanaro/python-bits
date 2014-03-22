#!/usr/bin/env python

import re, sys, string

def getitem(stuff, liststack):
    rflds = string.split(stuff)
    if rflds[0] == "sequence-item":
	item = "__elt_%s" % liststack[-1]
    elif rflds[0] == "sequence-start":
	item = "(__i_%s == 0)" % liststack[-1]
    elif rflds[0] == "sequence-length":
	item = 'len(__d[%s])' % `liststack[-1]`
    else:
	item = '__d[%s]' % `rflds[0]`

    if len(rflds) == 2 and rflds[1][0:4] == "fmt=":
	fmt = rflds[1][4:]
	if fmt == "url-quote": fmt = "urllib.quote"
    else:
	fmt = ""

    return item, fmt

def generate(fields):
    intro = re.compile(r"<!--# *(/?)(var|if|in|elif|else) *([^>]*)-->")
    liststack = []

    step = " "*4
    print "def dtmlfunc(**__d):"
    level = 1
    print "%simport sys, urllib" % (step*level)

    for i in range(len(fields)):
	pfx = fields[i][0:5]
	if pfx != "<!--#":
	    print '%ssys.stdout.write(%s)' % (step*level, `fields[i]`)
	else:
	    m = intro.match(fields[i])
	    if m is None:
		sys.stderr.write("Error: Unrecognized tag: %s\n" % fields[i])
		sys.exit(-1)
	    isclose = (m.group(1) != "")
	    tag = m.group(2)
	    rest = m.group(3)

	    if tag == "if":
		if isclose:
		    level = level - 1
		else:
		    item, fmt = getitem(rest, liststack)
		    print "%sif %s:" % (step*level, item)
		    level = level + 1

	    elif tag == "elif":
		level = level - 1
		item, fmt = getitem(rest, liststack)
		print "%selif %s:" % (step*level, item)
		level = level + 1

	    elif tag == "var":
		item, fmt = getitem(rest, liststack)
		if fmt:
		    print "%stry: sys.stdout.write(%s(%s))" % (step*level, fmt, item)
		    print "%sexcept: sys.stdout.write(%s.%s())" % (step*level, item, fmt)
		else:
		    print '%ssys.stdout.write("""%%s""" %% %s)' % (step*level, item)

	    elif tag == "else":
		level = level - 1
		print "%selse:" % (step*level)
		level = level + 1

	    elif tag == "in":
		if isclose:
		    level = level - 1
		    liststack = liststack[:-1]
		else:
		    flds = string.split(rest)
		    liststack.append(rest)
		    print "%s__i_%s = -1" % (step*level, flds[0])
		    if len(flds) == 2 and flds[1] == "mapping":
			print '%sfor __k_%s in __d[%s].keys():' % \
			      (step*level, rest, `rest`)
			level = level + 1
			print "%s__i_%s = __i_%s + 1" % (step*level, flds[0], flds[0])
			print "%s__elt_%s = __d[__k_%s]" % \
			      (step*level, rest, rest)
		    else:
			print '%sfor __elt_%s in __d[%s]:' % \
			      (step*level, rest, `rest`)
			level = level + 1

if __name__ == "__main__":
    fields = re.split(r"(<!--# */?(?:var|if|in|elif|else)[^>]*-->)", sys.stdin.read())
    generate(fields)
