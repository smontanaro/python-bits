"""

The soundex algorithm takes an English word, and returns an easily-computed
hash of it; this hash is intended to be the same for words that sound alike.
This module provides an interface to the soundex algorithm.

Note that the soundex algorithm is quite simple-minded, and isn't perfect by
any measure.  Its main purpose is to help looking up names in databases,
when the name may be misspelled -- soundex tends to group common
misspellings together.

Note that though the functions this module exports have the same names as
their counterparts in the original soundex module that was distributed with
Python, the algorithm is not quite the same.  In particular, the original
algorithm failed to notice doubled first letters (e.g., 'Lloyd').

You can vary the length of the soundex string calculated by setting the
module global, NDIGITS.  If you set NDIGITS to 0, it will compute a soundex
string whose length varies with a length of the input string.

"""

# Released to the public domain, by Skip Montanaro, 21 December 2000.

# This module represents a melding of two different soundex modules
# written by Tim Peters and Fred Drake.

NDIGITS = 3

# B for Break -- all characters assumed simply to break runs
_tran = ["B"] * 256
def _setcode(letters, value):
    for ch in letters:
        _tran[ord(ch.upper())] = _tran[ord(ch)] = value
_setcode("bfpv", "1")
_setcode("cgjkqsxz", "2")
_setcode("dt", "3")
_setcode("l", "4")
_setcode("mn", "5")
_setcode("r", "6")
# B for Break -- these guys break runs
_setcode("aeiouy", "B")
# I for Invisible -- they don't count for anything except as first char
_setcode("hw", "I")
assert len(filter(lambda ch: ch != "B", _tran)) == \
       (26 - len("aeiouy")) * 2, \
       "Soundex initialization screwed up"
_tran = "".join(_tran)
del _setcode

def get_soundex(name):
    """name -> Soundex code, following Knuth Vol 3 Ed 2 pg 394.

    The number of digits generated can be modified by setting the
    module-level variable, NDIGITS (default 3).
    """

    if not name:
        raise ValueError("soundex requires non-empty name argument")
    coded = name.translate(_tran)
    out = [name[0].upper()]
    lastrealcode = coded[0]
    ignore_same = 1
    for thiscode in coded[1:]:
        if thiscode == "B":
            ignore_same = 0
            continue
        if thiscode == "I":
            continue
        if ignore_same and lastrealcode == thiscode:
            continue
        out.append(thiscode)
        lastrealcode = thiscode
        ignore_same = 1
        if NDIGITS and len(out) > NDIGITS:
            break
    if len(out) < NDIGITS + 1:
        out.append("0" * (NDIGITS + 1 - len(out)))
    return "".join(out)

def get_soundex_orig(name):
    """Return the soundex hash value for a word.

    It will always be a 6-character string.  `name' must contain the word to
    be hashed, with no leading whitespace; the case of the word is ignored.
    This algorithm strives to be compatible with the algorithm in the old
    soundex.c module.

    """

    s = name.upper()
    if not s:
        return '000000'
    r = [s[0]]
    s = s[1:]
    while len(r) < 6 and s:
        c = s[0]
        s = s[1:]
        if c in "WHAIOUY":
            pass
        elif c in "BFPV":
            if r[-1] != '1':
                r.append('1')
        elif c in "CGJKQSXZ":
            if r[-1] != '2':
                r.append('2')
        elif c in "DT":
            if r[-1] != '3':
                r.append('3')
        elif c == "L":
            if r[-1] != '4':
                r.append('4')
        elif c in "MN":
            if r[-1] != '5':
                r.append('5')
        elif c == "R":
            if r[-1] != '6':
                r.append('6')
    r.append('0' * (6 - len(r)))
    return "".join(r)

def sound_similar(s1, s2):
    """Returns true if both arguments have the same soundex code."""
    return get_soundex(s1) == get_soundex(s2)

def _test():
    global nerrors, NDIGITS
    def check(name, expected):
        global nerrors
        got = get_soundex(name)
        if got != expected:
            nerrors = nerrors + 1
            print "error in Soundex test: name", name, \
                  "expected", expected, "got", got
    nerrors = 0
    NDIGITS = 3
    check("Euler", "E460")
    check("Ellery", "E460")
    check("guass", "G200")
    check("gauss", "G200")
    check("Ghosh", "G200")
    check("HILBERT", "H416")
    check("Heilbronn", "H416")
    check("Knuth", "K530")
    check("K ** n  U123t9247h   ", "K530")
    check("Kant", "K530")
    check("Lloyd", "L300")
    check("Liddy", "L300")
    check("Lukasiewicz", "L222")
    check("Lissajous", "L222")
    check("Wachs", "W200")
    check("Waugh", "W200")
    check("HYHYH", "H000")
    check("kkkkkkkwwwwkkkkkhhhhhkkkkemmnmnhmn", "K500")
    check("Rogers", "R262")
    check("Rodgers", "R326")
    check("Sinclair", "S524")
    check("St. Clair", "S324")
    check("Tchebysheff", "T212")
    check("Chebyshev", "C121")
    check("Bib", "B100")
    check("Bilbo", "B410")
    check("Bibby", "B100")
    check("Bibbster", "B123")

    if nerrors:
        raise SystemError("soundex test failed with " + `nerrors` +
                          " errors")
    else:
        print "all tests passed"
        
if __name__ == "__main__":
    _test()
