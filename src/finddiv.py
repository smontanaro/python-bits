
"""
Identify division operations in Python code

Usage: python finddiv.py *.py
"""

import tokenize
import sys
import glob

class TokenSorter:
    def __init__(self, f):
        self.tokens = {}
        self.filename = f
        self.line = ""
        self.linenumber = 0
        self.lastprinted = 0

    def tokeneater(self, typ, val, (sr, sc), (er, ec), line):
        if self.line != line:
            self.linenumber += 1
            self.line = line
        if (tokenize.tok_name[typ] == "OP" and
            val == "/" and
            self.lastprinted != self.linenumber):
            print "%s(%d): %s" % (self.filename, self.linenumber,
                                   line.rstrip())
            self.lastprinted = self.linenumber

def main():
    for arg in sys.argv[1:]:
        for fn in glob.glob(arg):
            try:
                f = open(fn)
            except IOError:
                pass
            else:
                ts = TokenSorter(fn)
                try:
                    tokenize.tokenize(f.readline, ts.tokeneater)
                except tokenize.TokenError:
                    pass

if __name__ == "__main__":
    main()
