#!/usr/local/bin/python

"""
A progress display module.

See the doc string for the Progress class for details.
"""

import sys, time

class Progress:
    """A class to display progress of an application.

    The Progress class is typically used to track the progress of
    long-running applications.  For instance, if you want to track a loop
    that executes thousands of iterations it might look like:

        import progress

        ticker = progress.Progress(title='Big Loop')
        for elt in big_list:
            calculate_something()
            ticker.tick()
        del ticker

    The output will look something like:

        Big Loop: .........1.........2.........3

    If you didn't want title, wanted to track not only the major and minor
    intervals but the average tick interval in milliseconds and number of
    seconds between major ticks, and set a major tick interval of 100 and
    minor tick interval of 25, you could instantiate the progress meter like

        ticker = progress.Progress(major=100, minor=25,
                                   majormark='<%(M)d,%(T).2fs,%(A)dms>',
                                   multiplier=1000)

    The output would then look something like:

        <1,1.01s,10ms>...<2,1.03s,10ms>...<3,1.02s,10ms>...<4,1.01s,10ms>

    Several formats for major and minor marks are understood - dictionary
    style string interpolation is used, so you can include as many or as few
    as you like and include arbitrary characters in mark format strings.
    The currently understood formats are:

    %(M) - the current major interval (integer)
    %(m) - the current minor interval (integer)
    %(T) - the clock time since the last major tick in seconds (float)
    %(t) - the clock time since the last minor tick in seconds (float)
    %(A) - the average clock time per tick since the last major tick in
           seconds (float)
    %(a) - the average clock time per tick since the last minor tick in
           seconds (float)

    The default minor mark is '.'.  The default major mark is '%(M)d'.  The
    default minor interval is 100 ticks.  The default major interval is 1000
    ticks.  Mark display can be suppressed by instantiating the progress
    meter with verbose=0.

    The units of the average tick time (default is seconds) can be changed
    by changing the multiplier.  For example, to change from seconds to
    milliseconds, set the multiplier argument to 1000 at instance creation.

    The default output stream is sys.stderr.  Any object that supports write
    and flush methods can be used.

    """
    def __init__(self, major=1000, minor=100, stream=sys.stderr, verbose=1,
                 title="", minormark=".", majormark="%(M)d", multiplier=1,
                 start=0):
        """create a progress meter

        argument	default		meaning
        major		1000		number of ticks between major marks
        minor		 100		number of ticks between minor marks
        stream		sys.stderr	where to write output (write & flush
        				required)
        verbose		1		non-zero means to display output
        title		''		string to display before ticking
        minormark	'.'		string to display to mark minor
        				intervals
        majormark	'%(M)d'		string to display to mark major
        				intervals
        multiplier	1		multiplier to apply for A or a formats
        """
        self.i = start
        self._T = self._t = 0
        self.multiplier = multiplier
        self.major = major
        self.minor = minor
        self.stream = stream
        self.minormark = minormark
        self.majormark = majormark
        self.verbose = verbose
        if self.verbose and title:
            self.stream.write(title+": ")
            self.stream.flush()
            
    def tick(self,majormark=None,minormark=None):
        """mark the passage of time"""
        if not self._t:
            # delay initializing the timers until the first tick
            # this avoids annoying first interval inaccuracies when using
            # the class interactively
            self._t = self._T = time.clock()
        self.i += 1
        if not self.verbose:
            return

        d = {
            # current Major interval
            "M": (self.i/self.major),
            # current minor interval
            "m": (self.i),
            # time since last Major tick
            "T": (time.clock()-self._T),
            # time since last minor tick
            "t": (time.clock()-self._t),
            # avg tick time since last Major tick
            "A": (time.clock()-self._T)*self.multiplier/self.major,
            # time since last minor tick
            "a": (time.clock()-self._t)*self.multiplier/self.minor,
            }

	if majormark is None: 
	    majormark = self.majormark
	if minormark is None:
	    minormark = self.minormark

        if self.i % self.major == 0:
            self.stream.write(majormark % d)
            self.stream.flush()
            self._T = time.clock()
        elif self.i % self.minor == 0:
            self.stream.write(minormark % d)
            self.stream.flush()
            self._t = time.clock()

    def __del__(self):
        if self.verbose:
            self.stream.write(" (%d)\n" % self.i)
            self.stream.flush()

    def value(self):
        return self.i

class Counter:
    """A counter which displays an ever increasing number in place"""

    def __init__(self, interval=10, stream=sys.stderr, start=0):
        self.counter = start
        self.interval = interval
        self.stream = stream

    def tick(self):
        self.counter += 1
        if self.counter % self.interval == 0:
            self.stream.write("\r%6d" % self.counter)
            self.stream.flush()

    def __del__(self):
        self.stream.write("\r%6d\n" % self.counter)
        self.stream.flush()

if __name__ == "__main__":
    import unittest
    import StringIO

    class CounterTestCase(unittest.TestCase):
        def test_by_tens(self):
            s = StringIO.StringIO()
            c = Counter(stream=s)
            c.tick()
            self.assertEqual(s.getvalue(), '')
            c.tick();c.tick();c.tick();c.tick();c.tick()
            c.tick();c.tick();c.tick();c.tick();c.tick()
            self.assertEqual(s.getvalue(), '\r    10')
            del c
            self.assertEqual(s.getvalue(), '\r    10\r    11\n')

            s = StringIO.StringIO()
            c = Counter(stream=s)
            c.tick();c.tick();c.tick();c.tick();c.tick()
            c.tick();c.tick();c.tick();c.tick()
            self.assertEqual(s.getvalue(), '')
            c.tick()
            self.assertEqual(s.getvalue(), '\r    10')
            del c
            self.assertEqual(s.getvalue(), '\r    10\r    10\n')

        def test_by_ones(self):
            s = StringIO.StringIO()
            c = Counter(stream=s, interval=1)
            c.tick()
            self.assertEqual(s.getvalue(), '\r     1')
            c.tick()
            self.assertEqual(s.getvalue(), '\r     1\r     2')
            del c
            self.assertEqual(s.getvalue(), '\r     1\r     2\r     2\n')

        def test_nonzero_start(self):
            s = StringIO.StringIO()
            c = Counter(stream=s, interval=1, start=3)
            c.tick()
            self.assertEqual(s.getvalue(), '\r     4')
            c.tick()
            self.assertEqual(s.getvalue(), '\r     4\r     5')
            del c
            self.assertEqual(s.getvalue(), '\r     4\r     5\r     5\n')

        def test_negative_start(self):
            s = StringIO.StringIO()
            c = Counter(stream=s, interval=1, start=-10)
            c.tick()
            self.assertEqual(s.getvalue(), '\r    -9')
            c.tick()
            self.assertEqual(s.getvalue(), '\r    -9\r    -8')
            del c
            self.assertEqual(s.getvalue(), '\r    -9\r    -8\r    -8\n')

    class ProgressTestCase(unittest.TestCase):
        def test_by_tens(self):
            s = StringIO.StringIO()
            c = Progress(stream=s)
            c.tick()
            self.assertEqual(s.getvalue(), '')
            for i in xrange(100):
                c.tick()
            self.assertEqual(s.getvalue(), '.')
            del c
            self.assertEqual(s.getvalue(), '. (101)\n')

            s = StringIO.StringIO()
            c = Progress(stream=s, minor=10)
            c.tick();c.tick();c.tick();c.tick();c.tick()
            c.tick();c.tick();c.tick();c.tick()
            self.assertEqual(s.getvalue(), '')
            c.tick()
            self.assertEqual(s.getvalue(), '.')
            del c
            self.assertEqual(s.getvalue(), '. (10)\n')

        def test_by_ones(self):
            s = StringIO.StringIO()
            c = Progress(stream=s, minor=1, major=10)
            c.tick()
            self.assertEqual(s.getvalue(), '.')
            c.tick()
            self.assertEqual(s.getvalue(), '..')
            for i in range(10):
                c.tick()
            self.assertEqual(s.getvalue(), '.........1..')
            del c
            self.assertEqual(s.getvalue(), '.........1.. (12)\n')

        def test_nonzero_start(self):
            s = StringIO.StringIO()
            c = Progress(stream=s, minor=1, start=3, major=10)
            c.tick()
            self.assertEqual(s.getvalue(), '.')
            c.tick()
            self.assertEqual(s.getvalue(), '..')
            for i in range(10):
                c.tick()
            del c
            self.assertEqual(s.getvalue(), '......1..... (15)\n')

        def test_negative_start(self):
            s = StringIO.StringIO()
            c = Progress(stream=s, minor=1, start=-10)
            c.tick()
            self.assertEqual(s.getvalue(), '.')
            c.tick()
            self.assertEqual(s.getvalue(), '..')
            del c
            self.assertEqual(s.getvalue(), '.. (-8)\n')

        def test_negative_start_small_major(self):
            s = StringIO.StringIO()
            c = Progress(stream=s, minor=1, major=5, start=-10)
            c.tick()
            self.assertEqual(s.getvalue(), '.')
            c.tick()
            self.assertEqual(s.getvalue(), '..')
            for i in range(10):
                c.tick()
            self.assertEqual(s.getvalue(), '....-1....0..')

    unittest.main()
