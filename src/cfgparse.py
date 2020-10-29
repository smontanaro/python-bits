#!/usr/bin/env python

"""
An alternative config file parser written in response to the ConfigParser
shootout: http://wiki.python.org/moin/ConfigParserShootout

Author: Skip Montanaro (skip@pobox.com)

Significant points:

    * File format is indentation-based (where'd he get that idea???)

    * Both attribute-style and dictionary-style access supported

    * File format is *not* compatible with Windows INI file
      - section introduced by line ending with colon (another brilliant
      coup!)
      - values are specified by simple key = value lines

    * Nesting to arbitrary depths is supported

    * Read and write with round trip, though comments are not currently
    preserved.

    * Proof-of-concept only - there's not much of an api yet - no
    sections(), has_section(), as_dict() methods, etc.  That should be easy
    enough to add later.

    * Typeless - everything's a string.  Python has plenty of ways to
    convert strings to other types of objects.

"""

import cStringIO as StringIO
import re

class Configuration(object):
    def __init__(self):
        self.__dict__['_Configuration__values'] = []

    def __cmp__(self, other):
        v1 = self.__values[:]
        v1.sort()
        v2 = self.__values[:]
        v2.sort()
        result = cmp(v1, v2)
        if result:
            return result
        for attr in v1:
            result = cmp(self[attr], other[attr])
            if result:
                return result
        return 0

    def __eq__(self, other):
        if isinstance(other, Configuration):
            return self.__cmp__(other) == 0
        return False

    def __getitem__(self, key):
        if key in self.__values:
            return self.__dict__[key]
        self.__dict__[key] = Configuration()
        self.__values.append(key)
        return self.__dict__[key]
    __getattr__ = __getitem__

    def __setitem__(self, key, val):
        self.__dict__[key] = val
        if key not in self.__values:
            self.__values.append(key)
    __setattr__ = __setitem__

    def write(self, fp):
        for attr in self.__values:
            item = self[attr]
            if isinstance(item, Configuration):
                subfp = StringIO.StringIO()
                item.write(subfp)
                fp.write("%s:\n" % attr)
                subfp.seek(0)
                for line in subfp:
                    fp.write(" "*4)
                    fp.write(line)
            else:
                fp.write("%s = %s\n" % (attr, item))

    def read(self, fp):
        for v in self.__values:
            delattr(self, v)
        self.read_helper(PushBackFile(fp), "")

    def read_helper(self, fp, indent):
        #print ">", id(self)
        for line in fp:
            mat = re.match(r'([ \t]*)(.*)$', line)
            left, right = mat.groups()
            if len(left) < len(indent):
                fp.push(line)
                #print "<", id(self)
                return

            if right[-1:] == ':':
                # new section
                section = right[:-1].strip()
                if not section:
                    raise ValueError, "Empty section, line %d" % fp.lineno
                cfg = self[section] = Configuration()
                newline = fp.next()
                fp.push(newline)
                if newline:
                    mat = re.match(r'([ \t]*)', newline)
                    if len(mat.group(0)) > len(indent):
                        cfg.read_helper(fp, mat.group(0))
            else:
                if '=' in right:
                    key, val = right.split('=', 1)
                else:
                    key, val = right, ""
                self[key.strip()] = val.strip()

    def __str__(self):
        return "<Configuration @ 0x%x>" % id(self)
    __repr__ = __str__

class PushBackFile(object):
    def __init__(self, fp):
        self.fp = fp
        self.stack = []
        self.lineno = 0

    def __iter__(self):
        return self

    def next(self):
        while True:
            if self.stack:
                line = self.stack.pop()
            else:
                line = self.fp.next()
            if line.strip()[:1] != "#":
                break
        if line:
            self.lineno += 1
        line = self.untab(line.rstrip())
        #print "+", line
        return line

    def push(self, line):
        if line:
            self.lineno -= 1
        #print "-", line.rstrip()
        self.stack.append(line)

    def untab(self, line):
        "expand tabs in leading whitespace to spaces"
        newline = []
        line = list(line)
        while line:
            c = line[0]
            del line[0]
            if c == " ":
                newline.append(" ")
            elif c == "\t":
                newline.append(" ")
                while len(newline) % 8:
                    newline.append(" ")
            else:
                newline.append(c)
                newline.extend(line)
                line = []
        return "".join(newline)

if __name__ == "__main__":
    import unittest

    class TestCase(unittest.TestCase):
        def test_cmp(self):
            cfg1 = Configuration()
            cfg1['level1'] = "new val"
            cfg2 = Configuration()
            cfg2['level1'] = "new val"
            self.assertEqual(cfg1, cfg2)
            cfg2['level1'] = "another val"
            self.assertNotEqual(cfg1, cfg2)

        def test_get_item(self):
            self.assertEqual(Configuration(), Configuration())
            cfg = Configuration()
            self.assertEqual(cfg['level1'], Configuration())

        def test_set_item(self):
            cfg = Configuration()
            cfg['level1'] = "new val"
            self.assertEqual(cfg['level1'], "new val")

        def test_set_item_2deep(self):
            cfg = Configuration()
            cfg['level1']['level2'] = "new val"
            self.assertEqual(cfg['level1']['level2'], "new val")

        def test_set_attr(self):
            cfg = Configuration()
            cfg.level1 = "new val"
            self.assertEqual(cfg.level1, "new val")

        def test_set_attr_2deep(self):
            cfg = Configuration()
            cfg.level1.level2 = "new val"
            self.assertEqual(cfg.level1.level2, "new val")

        def test_write(self):
            fp = StringIO.StringIO()
            cfg = Configuration()
            cfg.level1 = "new val"
            cfg.section1.item1 = "item 1"
            cfg.section1.subsection.item2 = "item 2"
            cfg.section2.subsection.item3 = "item 3"
            cfg['empty section1'] = Configuration()
            cfg['very last'] = "7"
            cfg.write(fp)
            self.assertEqual(fp.getvalue(), """\
level1 = new val
section1:
    item1 = item 1
    subsection:
        item2 = item 2
section2:
    subsection:
        item3 = item 3
empty section1:
very last = 7
""")

        def test_read(self):
            fp = StringIO.StringIO("""\
empty section1:
level1 = new val
section1:
# this is a comment for section1.item1:
    item1 = item 1
          # this is another comment
    subsection:
        item2 = item 2
section2:
    subsection:
        item3 = item 3
very last = 7
""")
            cfg = Configuration()
            cfg.read(fp)
            self.assertEqual(cfg._Configuration__values,
                             ['empty section1', 'level1',
                              'section1', 'section2', 'very last'])
            self.assertEqual(cfg.section1._Configuration__values,
                             ['item1', 'subsection'])
            self.assertEqual(cfg['empty section1'], Configuration())
            self.assertEqual(cfg.level1, "new val")
            self.assertEqual(cfg.section1.item1, "item 1")
            self.assertEqual(cfg.section1.subsection.item2, "item 2")
            self.assertEqual(cfg.section2.subsection.item3, "item 3")
            self.assertEqual(cfg['very last'], "7")

        def test_varying_indents(self):
            fp = StringIO.StringIO("""\
empty section1:
level1 = new val
section1:
	item1 = item 1
	subsection:
	    item2 = item 2
section2:
 subsection:
 	item3 = item 3
very last = 7
""")
            cfg = Configuration()
            cfg.read(fp)
            self.assertEqual(cfg._Configuration__values,
                             ['empty section1', 'level1',
                              'section1', 'section2', 'very last'])
            self.assertEqual(cfg.section1._Configuration__values,
                             ['item1', 'subsection'])
            self.assertEqual(cfg['empty section1'], Configuration())
            self.assertEqual(cfg.level1, "new val")
            self.assertEqual(cfg.section1.item1, "item 1")
            self.assertEqual(cfg.section1.subsection.item2, "item 2")
            self.assertEqual(cfg.section2.subsection.item3, "item 3")
            self.assertEqual(cfg['very last'], "7")

    unittest.main()
