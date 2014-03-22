#!/usr/local/bin/python

# create a directory tree of links whose names are DOS 8x3 that parallels
# the given tree

import os, string, sys, whrandom
from stat import *

def dosify(f, list):
    "return a DOSified version of f that doesn't already exist in list"
    flds = string.split(f, '.')
    if len(flds) > 2:
	flds = [string.join(flds[0:-1], '-'), flds[-1]]
    elif len(flds) == 1:
	flds.append('')

    if len(flds[0]) > 8 or len(flds[1]) > 3:
	# start with first 7 characters + last
	i = 7
	ext = flds[1][0:3]
	base = flds[0]
	newf = '%s.%s' % (base[0:i]+base[i-8:], ext)
	while i and newf in list:
	    i = i - 1
	    newf = '%s.%s' % (base[0:i]+base[i-8:], ext)

	# if that fails, simply use random three-digit numbers appended
	# to first five characters of base name
	if not i:
	    rnd = int(whrandom.random() * 999)
	    newf = '%s%03d.%s' % (base[0:5], rnd, ext)
	    while newf in list:
		rnd = int(whrandom.random() * 999)
		newf = '%s%03d.%s' % (base[0:5], rnd, ext)

	return newf

    return f

def frobulate(src, dst):
    'make links in dst for all files in src ensuring DOS 8x3 names'

    print src

    srcfiles = os.listdir(src)
    dstfiles = os.listdir(dst)
    mapping = []
    for f in srcfiles:
	shortf = dosify(f, dstfiles)
	mapping.append('%s --> %s\n' % (f, shortf))
	info = os.stat('%s/%s' % (src, f))
	if S_ISDIR(info[ST_MODE]):
	    os.mkdir('%s/%s' % (dst, shortf))
	    frobulate('%s/%s' % (src, f), '%s/%s' % (dst, shortf))
	else:
	    os.symlink('%s/%s' % (src, f), '%s/%s' % (dst, shortf))
	dstfiles.append(shortf)
    mapping.sort()
    open('%s/_MAPFILE.TXT' % dst, 'w').writelines(mapping)

def main():
    
    if len(sys.argv) < 3:
	sys.stderr.write('''\
Usage: dosname srcdir dstdir
  srcdir must be a directory
  dstdir must not exist
''')
	sys.exit(1)

    [src, dst] = sys.argv[1:3]

    if src[0] != '/':
	src = '%s/%s' % (os.getcwd(), src)
    if dst[0] != '/':
	dst = '%s/%s' % (os.getcwd(), dst)

    try:
	info = os.stat(src)
	if not S_ISDIR(info[ST_MODE]):
	    sys.stderr.write('Error - %s not a directory\n' % src)
	    sys.exit(1)
    except os.error:
	sys.stderr.write('Error - %s does not exist\n' % src)
	sys.exit(1)

    try:
	info = os.stat(dst)
	sys.stderr.write('Error - %s already exists\n' % dst)
	sys.exit(1)
    except os.error:
	os.mkdir(dst)

    frobulate(src, dst)

if __name__ == '__main__': main()
