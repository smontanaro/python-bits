# Skip's Python Bits #

This repository just contains a bunch of little Python odds-n-ends I used to
keep on my now defunct personal website. This page is just a recast of what
used to be the index.html file for the Python section of that site. **If
something looks a bit out-of-date, note the dates!**


## [at(1) front end](at.py) ##

I use the at(1) command from time-to-time, and everything works well if I
just need to run a command a bit in the future on the current day, e.g., "at
21:00".  I use it rarely enough, however, that I can never remember the
timespec format necessary if the time to execute is some number of days in
the future.  I always wind up picking through the man page.  This simple
front-end accepts whatever the `dateutil.parser` can parse and builds the
somewhat baroque timespec which the at(1) command demands.

## [CSV-to-CSV filter](csv2csv.py) ##

This is a handy little script to extract columns from a CSV file
and/or normalize the structure of a CSV file to compare different
versions.

## [Finite State Machine](fsm.py) ##

I cleaned this up a bit and brought it a bit more into the 21st
century (class exceptions, a simple doctest, use `in` instead of
calling `has_key()`, etc).  (last updated 2010-04-24)

## [Simple Logging Wrapper for prstat](prstat-t.py) ##

`prstat` is the Solaris version of `top`.  Where I used to work we used to
use top as a crude logging tool, just letting it run with output redirected
to a rotating set of logfiles.  `prstat` can **almost** substitute for top
in this context, however it doesn't timestamp its output.  `prstat-t.py`
solves that shortcoming.  (last updated 2009-09-14)

## [Minimalist Mailman Review Page](mmfold.py) ##

If you manage a popular mailing list with Mailman these days, you know how
hard it can be to review the messages that get held for your review.
`mmfold.py` fetches the review page for a mailing list and presents a more
condensed version of the review page in your web browser.  The new version
accepts password info in the URL.  (last updated 2008-06-30)

## [zipargs function for shell scripts](zipargs.sh) ##

<dd> A colleague wanted to perform a zip operation (Python's
<code>zip</code> not the compression program of the same name) in a
shell script.  So I wrote something for him.  Of course, it uses
Python's <code>zip()</code> function under the covers. </dd>

## [Introspective <code>dir()</code> function](dir.py) ##

<dd>If you use the <code>dir()</code> function as a cheap instrospection
tool, you've probably noticed that it doesn't work very well for exploring
package hierarchies.  Here's a replacement which roots
around in package directories and eggs and lets you know what submodules and
packages it contains. (last updated 2008-03-18)

## [bsddb185 module](http://pypi.python.org/pypi/bsddb185) ##

Python 3.x no longer comes with the bsddb185 module.  While it's rarely
used, it does have some use on systems which still use the Berkeley DB 1.85
library, mostly BSD-derived Unix systems (including Macs).  I extracted the
module from the current trunk (2.6a0) and stuck it on PyPI.

## [Lock resources](http://pypi.python.org/pypi/lockfile) ##

Python has a couple different file locking APIs.  None are portable.  The
lockfile package implements a cross-platform API and three different classes
which use that API. (I no longer maintain the lockfile package.)

## [Add or print iCal events](ical.py or todos from the) command line ##

I use a Powerbook but rarely take it to work.  This makes it difficult to
manage events and todos with iCal.  The [appscript module](http://freespace.virgin.net/hamish.sanderson/appscript.html) makes
it fairly easy to script many Mac OSX applications from
Python.  [ical.py](ical.py) is a fairly simple example of appscript usage.
It also relies on the [dateutil package](http://labix.org/python-dateutil) to support flexible date/time parsing.

## [Queue based on sockets](SocketQueue.py) ##

A thread on `comp.lang.python` got into a discussion of
communication between multiple processes.  I suggested creation of a
class like Python's threaded Queue class.  [SocketQueue.py](SocketQueue.py) is a trivial implementation of
the idea.  (last updated 2005-09-28)

## [Mmencode in Python](mmencode.py) ##

Way back in the early days of MIME there was mmencode.  It was a classical
Unix filter.  It was small and did one thing well.  Somewhere along the way
it got replaced by other tools and on my latest web server I found it's not
available (at least not without grubbing around for the proper RPM).  Here's
a [simple replacement](mmencode.py) in Python.  It only implements the `-q`
and `-u` flags and only writes to stdout, but that probably accounts for 99%
of the usage. (last updated 2005-08-12)

## [Autoload modules](autoload.py) ##

Someone on `comp.lang.python` whose name I didn't record came up with this
nifty [module autoloader](autoload.py).  I modified it slightly. (last
updated 2005-03-16)

## [Config file reader/writer](cfgparse.py) ##

In response to
a [ConfigParser Shootout](http://www.python.org/moin/ConfigParserShootout) I
wrote one such [little beastie](cfgparse.py).  Its main features
are: indentation-based file format, nesting to arbitrary depth, read/write
round trip (sans comments at the moment) and attribute-style or dict-style
access. (last updated 2004-10-22)

## [Rebind global variables during `reload()`](super_reload.py) ##

The subject of the
[behavior of the `reload()` function](http://groups.google.com/groups?hl=en&lr=&ie=UTF-8&oe=UTF-8&threadm=mailman.322.1079113337.19534.python-list%40python.org&rnum=1&prev=/groups%3Fq%3Dpython%2Bdeprecating%2Breload%26hl%3Den%26lr%3D%26ie%3DUTF-8%26oe%3DUTF-8%26selm%3Dmailman.322.1079113337.19534.python-list%2540python.org%26rnum%3D1) came
up in `comp.lang.python`.  This [trival implementation](super_reload.py) may
cover most of the perceived shortcomings of the builtin `reload()`.  (last
updated 2004-03-14)

## [Decode strings heuristically](decodeh.py) ##

When dealing with Unicode inputs from various sources you may or may not
know how the input is encoded.  If you don't know you probably have to
guess.  This [little module](decodeh.py) demonstrates one set of
guesses.  You will almost certainly want to modify it for your needs.  (last
updated 2004-03-01)

## [Session save/restore](save_session.py) ##

Gerrit Holl suggested save() and load() builtins on python-dev.  He was
thinking about using pickles, but I implemented
a [simpleminded version](save_session.py) using the readline module.
Unfortunately, the readline requirement means it won't work on Windows.
Feel free to fix that shortcoming.  (last updated 2003-12-01)</dd>

## [Simple progress meter](progress.py) ##

For long-running calculations, it's nice to have a simple way to display
progress.  [progress.py](progress.py) provides a couple classes to support
this.  (last updated 2004-01-24)

## [Latin-1-to-ASCII codec](latscii.py) ##

From time-to-time you really, really, really just want ASCII, as when some
spammer sends you a message with the subject, "We cän makë it lönger now" or
"keep up th¯e strugglê, get out ¨of that mess" (whatever that
means).  [latscii.py](latscii.py) is a simple codec which makes a reasonable
attempt to strip accents from Latin-1 letters and map other characters to
reasonable ASCII equivalents (such as mapping '¡' to '!').  (last updated
2003-11-11)

## [Regular expressions as dictionary keys](REDict.py) ##

The topic of using regular expressions as dictionary
keys
[recently](http://groups.google.com/groups?hl=en&lr=&ie=UTF-8&oe=UTF-8&threadm=1f0bdf30.0308202049.7d251469%40posting.google.com&rnum=2&prev=/groups%3Fq%3Dregular%2Bexpression%2Bdictionary%2Bkey%2Bgroup:comp.lang.python.*%26hl%3Den%26lr%3D%26ie%3DUTF-8%26oe%3DUTF-8%26group%3Dcomp.lang.python.*%26selm%3D1f0bdf30.0308202049.7d251469%2540posting.google.com%26rnum%3D2) on
`comp.lang.python`.  (It's also come
up
[in the past](http://groups.google.com/groups?hl=en&lr=&ie=UTF-8&oe=UTF-8&threadm=3C0B2DE9.5040308%40home.com&rnum=1&prev=/groups%3Fhl%3Den%26lr%3D%26ie%3DUTF-8%26oe%3DUTF-8%26selm%3D3C0B2DE9.5040308%2540home.com).)
I had a need for this, but with dictionaries containing hundreds of keys,
all the regular expression matching makes the straightforward implementation
a dog.  `REDict.REDict` uses a binary search of the keys to speed things up.
`has_key()` is `O(log len(d))` instead of `O(len(d))`.  Using the
`REDict.FastREDict` class, matching is more like O(1).  More could probably
be done (caching compiled regular expressions or optimizing the large
generated regular expressions), but this suffices for the time being.  (last
updated 2003-10-22)

## [Bulk Discard of Queued Mailman Messages](mmdiscard.py) ##

A recent virus attack left me trying to manually discard a thousand or so
messages per day for a Mailman-2.1 list I help administer.  I wrote
`mmdiscard.py` to deal with that from the command line. (last updated
2003-10-15)

## [Date-parsing module](dates.py) ##

I wrote this module a long time ago. Use `dateutil` instead.

## [Readline & command history](completions.py) ##

2002-11-08.  I refer to this during interactive startup (one of the files
which gets imported via PYTHONSTARTUP.  It's a useful file and also
demonstrates how to use the `atexit` module.

## [Marshal written in Python](marshalp.py) ##

Guido sent me a version of the marshal module written in Python over fifteen
years ago.  (I no longer remember why.)  Once when I encountered a corrupted
marshal file I modified it to not raise an exception when encountering an
error during load().  Instead it returns what it has accumulated up to that
point.  **Warning: Do not install this as marshal.py!  If you do, you
will almost certainly live to regret that mistake!**

## [Alarms for asyncore](alarms.py) ##

2002-01-23.  I recently had a reason to start using asyncore.  It's a
marvelous package for doing I/O with several network sockets.  One of the
first things I wanted to do after getting it working was implement alarms.
Signal.alarm is ugly and may not work everywhere anyway, so I took advantage
of the fact that asyncore uses the timeout feature of select() and poll().

## [Weekend Edition Sunday Puzzle](nprpuzzle.py) ##

2001-10-14.  I listen on occasion to NPR's [Sunday Weekend Edition](http://www.npr.org/programs/wesun/).
Perhaps the best segment of the show is the [Puzzle](http://www.npr.org/programs/wesun/puzzle/) run by Will
Shortz.  On October 7th, 2001, this challenge was posted:

> Draw a 4 by 3 box. The object is to fill it with letters
> spelling 3 four-letter words across and 4 three-letter words reading
> down. The conditions:  your box can not repeat any letters, and it
> must use all six vowels (a, e, i, o, u, y) once. All words must be
> uncapitalized, common English words.

The code in <a href="nprpuzzle.py">nprpuzzle.py</a> solves this problem
using a straightforward O(N**3) algorithm.  I don't claim it's the best way
to approach the problem, but it was a fun diversion for a Sunday.  It uses
my little [progress module](progress.py) to track progress.

## [Locate Division Operators](finddiv.py) ##

2001-08-13.  With the coming change to
the
[semantics of integer division](http://python.sourceforge.net/peps/pep-0238.html) you'll
probably want to run something like finddiv.py over your code to identify
potential trouble spots.  It does nothing more than identify lines
containing a "/" operator.  It doesn't perform any analysis to try and
prune the possible list of lines it displays.  It does display lines in a
format that Emacs's next-error command understands.

## [ConstantMap.py - map numeric constants to their names](ConstantMap.py) ##

The `ConstantMap.ConstantMap` class can be instantiated from modules of
constants to map "magic numbers" back to their names.  This is useful when
debugging code that returns such numbers.  For example, the numeric constant
modules generated by the h2py script all map semi-meaningful names to mostly
meaningless numbers.  ConstantMap allows you to map them back. (last updated
2004-03-07)

## [Watch - keyboard/mouse monitor](http://sourceforge.net/projects/watch/) ##

This Python script monitors keyboard and mouse activity and enforces work
and rest times.  It currently only runs on Linux, but it has run on Windows
in the past (only directly monitoring mouse activity) and could probably run
on the Mac without a lot of effort.

## [Soundex module](soundex.py) ##

2000-12-22.  This module is a Python replacement for the now
defunct [soundex.c](soundex.c).  This module is a merging of separate ones
written by Tim Peters and Fred Drake.

## [SYLK file reader](sylk.py) ##

2000-10-10.  This module reads SYLK files and generates CSV files.  Note
that it currently has only been tested with files generated from AppleWorks
5.0 on a Mac.

## [Rough Size Calculator](sizer.py) ##

2000-09-27.  There are three general sources of memory leaks in long-running
Python programs: cyclical objects that reference counting can't reclaim,
botches at the low-level malloc interface, and growth of container objects
that are reachable, but whose growth you're unaware of.  Neil Schemenauer's
garbage collector in Python 2.0 does a good job identifying cyclical
garbage.  This module attacks the hird case.  The test case uses the Cache
module below.

## [Simple Caching Dictionary](Cache.py) ##

2000-09-27.  Sometimes you need to cache results of long computations or
database queries, but don't want your memory consumption to grow without
bound.  The Cache class subclasses `UserDict.UserDict` to provide a cache
which discards values based on access time.

## [XML-RPC validation suite](xmlrpcserver.py) ##

2000-06-05.  This server passes the XML-RPC validation suite as
implemented at [validator.xmlrpc.com](http://validator.xmlrpc.com/) as of June
5th, 2000.

## Adding [gzip encoding capability](gzip-xmlrpc.txt) to XML-RPC clients and servers ##

2000-04-19.  The instructions in [gzip-xmlrpc.txt](gzip-xmlrpc.txt) describe
simple mods to XML-RPC servers and clients to allow responses to be encoded
using gzip when possible.  This can help performance significantly when
using XML-RPC over wide area networks.  You can also download the version of
<a href="xmlrpclib.py">xmlrpclib.py</a> that I use which includes one or two
other mods.  It is based on version 0.9.8 of Fredrik Lundh's [xmlrpclib](http://www.pythonware.com/products/xmlrpc/)
package.
