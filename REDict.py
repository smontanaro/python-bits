#!/usr/bin/env python

"""
REDict - a dictionary whose keys are regular expressions.

The user probes the dictionary with strings, but the keys are strings
treated as regular expressions.  For example, if you defined a REDict()
object like so:

    contacts = REDict()
    contacts['.*python\.org'] = ('Barry', 'barry@python.org')
    contacts['.*mojam\.com'] = ('Skip', 'skip@mojam.com')

then

    contacts['www.mojam.com'] == ('Skip', 'skip@mojam.com')
    contacts['mail.python.org'] == ('Barry', 'barry@python.org')

Note that a probe of the dictionary is not guaranteed to always return a
unique key.  Consider:

    d = REDict()
    d['a+c'] = 'a-plus-c'
    d['aaac'] = 'a-a-a-c'

This is true:

    d['aaac'] in ['a-plus-c', 'a-a-a-c']

but this may not be:

    d['aaac'] == 'a-a-a-c'

even within the same program, since the order of d.keys() is not defined.
If you desire/require the same key to map to the same slot repeatedly in the
face of multiple possible regular expression matches, try the FastREDict
class.  It caches the actual key which matches a given input key.  So long
as you don't delete the regular expression key from the dictionary, repeated
probes of the dictionary for a given input key will map to the same actual
key.

Note: Regular expressions are only used when probing an REDict.  For
setting, deleting or popping elements from an REDict, normal dictionary
behavior is used.

Note: In theory, you can also work things the other way.  The keys can be
constant strings and the dictionary probed using a regular expression.  It's
less obvious that the semantics of such an arrangement behave as much like
regular dictionaries as this scheme does.  It's also more difficult
(impossible?) to avoid linear search of the keyspace in all situations.  You
can construct a string from the keys like so:

    def _get_exact_key(self, key):
        keystr = SEP+SEP.join(self.keys())+SEP
        return random.choice(re.findall(SEP+key+SEP, keystr))[1:-1]

but it becomes difficult to choose SEP.  SEP must be a sequence which won't
appear in probes.  What if the user asks for d['.*']?  Well, you could
change all occurrences of'.*' to '[^'+SEP+']' if SEP is a single character
string.  That's unsatisfying however.  Other "match a lot of stuff" strings
can also trip you up.  Multi-character separators are no better.  In the
end, I think you're stuck with the slow but safe choice:

    def _get_exact_key(self, key):
        for candidate in self.keys():
            if re.match(key, candidate):
                return candidate

The FastREDict class is also much faster than the REDict class.  Once a
match for a specific input key is found, the same match is reused as long as
that match remains a key in the underlying dictionary.  For largely static
dictionaries which are probed many times using the same keys this can speed
up access tremendously.  Try executing this module as a standalone script
and give it the -t flag (uses the timeit module, so this feature is
available only in Python 2.3 or later).
"""

import re
import sys

_VERB = False

__all__ = ["REDict", "FastREDict"]

class REDict(dict):
    """A dictionary whose keys are regular expressions."""

    def _get_exact_key(self, key):
        """return an actual key which re matches the input key"""
        keys = self.keys()
        while len(keys) > 1:
            # minimize the number of matches necessary by using binary search
            mid = len(keys)/2
            if _VERB: print >> sys.stderr, (key, mid, keys[:mid], keys[mid:]),
            lowkeys = keys[0:mid]
            if lowkeys and re.match('|'.join(lowkeys), key) is not None:
                if _VERB: print >> sys.stderr, "l",
                keys = lowkeys
            else:
                highkeys = keys[mid:]
                if re.match('|'.join(highkeys), key) is not None:
                    if _VERB: print >> sys.stderr, "h",
                    keys = highkeys
                else:
                    if _VERB: print >> sys.stderr, "f",
                    keys = []
        if keys:
            if _VERB: print >> sys.stderr, keys[0]
            return keys[0]
        if _VERB: print >> sys.stderr
        raise KeyError, "%s does not re match any actual key" % key

    def get(self, key, fail=None):
        if key in self:
            return self[key]
        else:
            return fail

    def has_key_exact(self, key):
        return dict.has_key(self, key)

    def has_key(self, key):
        """re.match against a bunch of alternatives.

        Return True if any match.  Could be faster if we didn't mind a bit
        of code duplication.
        """
        try:
            self._get_exact_key(key)
        except KeyError:
            return False
        else:
            return True

    __contains__ = has_key

    def __getitem__(self, key):
        k = self._get_exact_key(key)
        return dict.__getitem__(self, k)

    def __setitem__(self, key, value):
        """Set an item in the dictionary.

        Note that we don't use regular expressions here!
        """
        if not isinstance(key, (str, unicode)):
            raise TypeError, "%s is not a string type" % key
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        """Delete an item from an REDict.

        Note that regular expressions aren't used here!
        """
        if not isinstance(key, (str, unicode)):
            raise TypeError, "%s is not a string type" % key
        dict.__delitem__(self, key)

class SlowREDict(REDict):
    """A version of REDict which uses linear search.

    Just for demonstration and testing - do not use!
    """

    def _get_exact_key(self, key):
        """return an actual key which re matches the input key"""
        keys = self.keys()
        for k in keys:
            if re.match(k, key) is not None:
                return k
        raise KeyError, "%s does not re match any actual key" % key

class FastREDict(REDict):
    """A version of REDict which remembers what specific keys matched."""
    def __init__(self, *args):
        REDict.__init__(self, *args)
        self._cache = {}
        self.true_counts = self.counts = 0

    def _get_exact_key(self, key):
        self.true_counts += int(key in self._cache)
        self.counts += 1
        if key in self._cache:
            return self._cache[key]
        k = REDict._get_exact_key(self, key)
        self._cache[key] = k
        return k

    def __delitem__(self, key):
        REDict.__delitem__(self, key)
        delkeys = [k for k in self._cache if self._cache[k] == key]
        for k in delkeys:
            del self._cache[k]

    def __del__(self):
        if _VERB:
            print self.counts, self.true_counts

if __name__ == "__main__":
    import unittest

    do_timing = False

    args = sys.argv[1:]
    for arg in sys.argv[1:]:
        if arg == "-v":
            _VERB = True
        elif arg == "-t":
            args.remove("-t")
            do_timing = True
    sys.argv[1:] = args

    class REDictTests(unittest.TestCase):
        def new_dict(self):
            return REDict()

        def assertContains(self, el, seq):
            self.assertTrue(el in seq)

        if not hasattr(unittest.TestCase, "assertTrue"):
            assertTrue = unittest.TestCase.failUnless
            assertFalse = unittest.TestCase.failIf

        def test_get_exact_key(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            self.assertRaises(KeyError, d._get_exact_key, "d")
            self.assertNotEqual(d._get_exact_key("abbbc"), "abc")

        def test_get(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            self.assertEqual(d.get("d"), None)
            self.assertEqual(d.get("abbbc"), "ab+c")

        def test_multi_matches(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            d["a*b+c"] = "a*b+c"
            d["b+c"] = "b+c"
            self.assertEqual(d.get("d"), None)
            self.assertEqual(d.get("aabbbbbbc"), "a*b+c")
            self.assertContains(d.get("bbc"), ["a*b+c", "b+c"])

        def test_repeated_matches(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            d["a*b+c"] = "a*b+c"
            d["b+c"] = "b+c"
            self.assertEqual(d.get("aabbbbbbc"), "a*b+c")
            self.assertEqual(d.get("aabbbbbbc"), "a*b+c")

        def test_delete_key(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            d["a*b+c"] = "a*b+c"
            d["b+c"] = "b+c"
            self.assertEqual(d.get("aabbbbbbc"), "a*b+c")
            del d["a*b+c"]
            self.assertEqual(d.get("aabbbbbbc"), None)

        def test_contains(self):
            d = self.new_dict()
            d["abc"] = "abc"
            d["ab+c"] = "ab+c"
            d["a*b+c"] = "a*b+c"
            d["b+c"] = "b+c"
            self.assertFalse("d" in d)
            self.assertTrue("bc" in d)

        def test_set(self):
            d = self.new_dict()
            self.assertRaises(TypeError, d.__setitem__, 1, "1")
            self.assertEqual(d.__setitem__(u"1", "1"), None)

    class SlowREDictTests(REDictTests):
        def new_dict(self):
            return SlowREDict()

    class FastREDictTests(REDictTests):
        def new_dict(self):
            return FastREDict()

    if do_timing:
        import timeit
        setup = """\
import __main__
d = __main__.%s()
for i in range(100):
    d[str(i)] = str(i)
"""
        # Figure out what the middle key is so we are always testing average
        # case behavior for SlowREDict (on average we have to search half
        # way through the dict to find a key).
        d = {}
        # cap the size at 100 since that's how many compiled re's the sre
        # module remembers - greater than that we're testing the speed of
        # the written-in-Python sre_compile module
        for i in range(100):
            d[str(i)] = str(i)
        middle = d.keys()[len(d)/2]

        stmt = "x = '%(middle)s' in d" % locals()

        number = 500
        t = timeit.Timer(stmt=stmt, setup=setup%"FastREDict")
        print "FastREDict: %.2f usec/pass (n=%d)" % \
              (1000000 * t.timeit(number=number)/number, number)
        t = timeit.Timer(stmt=stmt, setup=setup%"REDict")
        print "REDict: %.2f usec/pass (n=%d)" % \
              (1000000 * t.timeit(number=number)/number, number)
        t = timeit.Timer(stmt=stmt, setup=setup%"SlowREDict")
        print "SlowREDict: %.2f usec/pass (n=%d)" % \
              (1000000 * t.timeit(number=number)/number, number)

    unittest.main()
