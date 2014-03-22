#!/usr/local/bin/python

import urllib, re, sys, time
import MySQLdb, MySQLdb.cursors

(dbhost, dbuser, dbpwd) = ("localhost", "username", "password")

### pulled from another module I have locally ...

def table_row(data, tpat=re.compile('(<(?P<sl>/)?(?P<tag>t[rdh]|table)[^>]*>)', re.I)):
    """reorganize a web page so that each table row is on one line"""
    data = re.sub(r"[\r\n]+", " ", data)
    data = re.sub(r"(?i)\s*<(/?)td[^>]*>\s*", r"<\1td>", data)
    data = re.sub(r"(?i)\s*<(/?)th[^>]*>\s*", r"<\1th>", data)
    data = re.sub(r"(?i)\s*<tr[^>]*>\s*", "\n<tr>", data)
    data = re.sub(r"(?i)\s*</tr[^>]*>\s*", "</tr>\n", data)
    data = re.sub(r"(?i)\s*<(/?)table[^>]*>\s*", r"\n<\1table>\n", data)
    return data

def _zap_esc_map(sub, _epat = re.compile(r'(\[\anrfbtv])')):
    """map C-style escape sequences to literal values"""
    for craw, cmap in [(r'\n', '\n'), (r'\\', '\\'), (r'\r', '\r'),
                       (r'\t', '\t'), (r'\f', '\f'), (r'\a', '\a'),
                       (r'\b', '\b'), (r'\v', '\v')]:
        if _epat.search(sub) is None:
            return sub
        sub = re.sub(craw, cmap, sub)
    return sub

def zaptags(data, *tags):
    """delete all tags (and /tags) from input data given as arguments"""
    for pat in tags:
        pat = pat.split(":")
        sub = ""
        if len(pat) >= 2:
            sub = pat[-1]
            pat = ":".join(pat[:-1])
        else:
            pat = pat[0]
            sub = ""
        if '\\' in sub:
            sub = _zap_esc_map(sub)
        data = re.sub(r'(?i)</?(%s)(?:\s[^>]*)?>'%pat, sub, data)
    return data

_entities = {
	     '&Aring;': 'A',
	     '&Auml;': 'A',
	     '&Ccedil;': 'C',
	     '&Eacute;': 'E',
	     '&Egrave;': 'E',
	     '&Iacute;': 'I',
	     '&Oslash;': 'O',
	     '&Ouml;': 'O',
	     '&Uuml;': 'U',
	     '&amp;': '&',
	     '&aring;': 'a',
	     '&auml;': 'a',
	     '&ccedil;': 'c',
	     '&copy;': '',
	     '&eacute;': 'e',
	     '&egrave;': 'e',
	     '&gt;': '>',
	     '&iacute;': 'i',
	     '&lt;': '<',
	     '&nbsp;': ' ',
	     '&ntilde;': 'n',
	     '&oslash;': 'o',
	     '&ouml;': 'o',
	     '&quot;': '"',
	     '&reg;': '',
	     '&uuml;': 'u',
	     '&#160;': ' ',
	     '&#150;': '-',
	     '&#151;': '-',
	     '&#145;': "`",
	     '&#146;': "'",
	     '&#149;': "*",
	     '&#174;': "",
	     '&#183;': " ",
	     '&#200;': "e",
	     }

_entitypat = re.compile(r'(\&(?:[A-Za-z]+|#[0-9]+);)')
_numentitypat = re.compile(r'(\&#[0-9]+;)')

_8bitchars = {
    '\222': "'",
    '\225': "*",
    '\262': '"',
    '\263': '"',
    '\271': "'",
    '\272': "'",
    '\213': "<",
    '\214': "'",
    '\223': '"',
    '\224': '"',
    }

_8bitpat = re.compile('[%s]' % "".join(_8bitchars.keys()))

def map_entities(line):
    if _entitypat.search(line) is not None:
        # whack leading zeroes from numeric entities
        line = re.sub(r"&#0+([0-9]+);", r"\&#\1;", line)
	for k in _entities.keys():
            if _entitypat.search(line) is None:
                break
	    line = re.sub(k, _entities[k], line)
    line = _numentitypat.split(line)
    for i in range(len(line)):
        if not i%2: continue
        line[i] = chr(int(line[i][2:-1]))
    line = "".join(line)
    if 0 and _entitypat.search(line) != None:
	sys.stderr.write('Line still contains entities: &%s;\n' %
                         _entitypat.group(1))
    for k in _8bitchars.keys():
        if _8bitpat.search(line) == None:
            break
        line = re.sub(k, _8bitchars[k], line)
    return line

### start of getpybugs proper ...

def get_current_from_sf(urlfmt):
    offset = 0
    incr = 50

    itempat = re.compile(r"""<td>\s*(?P<id>[0-9]+)"""
                         r"""<td>\s*(?P<summary>[^<]+)"""
                         r"""<td>\s*\*?\s*(?P<submit_time>[^<]+)"""
                         r"""<td>\s*(?P<assignee>[^<]+)"""
                         r"""<td>\s*(?P<submitter>[^<]+)$""",
                         re.I)

    text = []
    while not text or text[-1].find("Next 50") != -1:
        f = urllib.urlopen(urlfmt % offset)
        offset += incr
        text.append(f.read())

    rows = table_row("\n".join(text)).split("\n")

    data = {}
    for row in rows:
        row = map_entities(row)
        row = zaptags(row, "b", "a", "tr", "/td", "input")
        mat = itempat.match(row)
        if mat is not None:
            data[int(mat.group("id"))] = mat.groupdict()
    return data

def get_local_from_db(table):
    db = MySQLdb.Connection(host=dbhost, user=dbuser, passwd=dbpwd,
                            db="pythonbugs",
                            cursorclass=MySQLdb.cursors.DictCursorNW)

    c = db.cursor()

    # get existing bugs
    local = {}
    c.execute("select id,summary,submit_time from %s" % table)
    rows = c.fetchall()
    for row in rows:
        local[int(row["id"])] = row

    db.close()
    
    return local

def compute_changes(current, local):
    """compute new, closed, and continuing items"""
    # current is info fetched from SF, local is from MySQL
    closed = {}
    new = {}
    continuing = {}
    for key in local:
        if key in current:
            continuing[key] = current[key]
        else:
            closed[key] = local[key]
    for key in current:
        if key not in local:
            new[key] = current[key]

    return new, closed, continuing

def update_local(new, closed, continuing, table):
    db = MySQLdb.Connection(host=dbhost, user=dbuser, passwd=dbpwd,
                            db="pythonbugs",
                            cursorclass=MySQLdb.cursors.DictCursorNW)

    c = db.cursor()

    for key in new:
        item = new[key]
        c.execute("insert into %s"
                  "  (id, summary, submit_time, assignee, submitter)"
                  "  values"
                  "  (%%s, %%s, %%s, %%s, %%s)" % table,
                  (key, item["summary"], item["submit_time"],
                   item["assignee"], item["submitter"]))

    for key in closed:
        if c.execute("delete from %s where id=%%s" % table, (key,)) == 0:
            print >> sys.stderr, "deleted no records for", key

    for key in continuing:
        item = continuing[key]
        c.execute("update %s"
                  "  set summary=%%s,"
                  "      assignee=%%s"
                  "  where id=%%s" % table,
                  (item["summary"], item["assignee"], key))
        
def print_summary(dict, title, detailfmt):
    keys = dict.keys()
    keys.sort()
    print
    print title
    print "-"*len(title)
    print
    for key in keys:
        print dict[key]["summary"],
        print "(%s)" % str(dict[key]["submit_time"]).split()[0]
        print "\t"+detailfmt%key
    
def howmany():
    db = MySQLdb.Connection(host=dbhost, user=dbuser, passwd=dbpwd,
                            db="pythonbugs",
                            cursorclass=MySQLdb.cursors.DictCursorNW)

    c = db.cursor()
    nbugs = c.execute("select * from openbugs")
    npatches = c.execute("select * from openpatches")
    db.close()

    return (nbugs, npatches)

def main():
    projurl = "http://sourceforge.net/projects/python"
    
    bugurlfmt = ("http://sourceforge.net/tracker/index.php?"
                 "group_id=5470&atid=105470&set=custom&_assigned_to=0&"
                 "_status=1&_category=100&_group=100&order=artifact_id&"
                 "sort=ASC&offset=%d")

    patchurlfmt = ("http://sourceforge.net/tracker/index.php?"
                   "group_id=5470&atid=305470&set=custom&_assigned_to=0&"
                   "_status=1&_category=100&_group=100&order=artifact_id&"
                   "sort=ASC&offset=%d")

    detailfmt = "http://python.org/sf/%d"

    countpat = re.compile(r"(?P<tag>Bugs|Patches)</A>\s*"
                          r"\(\s*<B>(?P<open>[0-9]+)\s*open\s*/"
                          r"\s*(?P<total>[0-9]+)\s*total\s*</B>\s*\)<BR>",
                          re.I)
    proj_text = table_row(urllib.urlopen(projurl).read())
    counts = countpat.findall(proj_text)
    counts.sort()

    nbugs, npatches = howmany()

    deltabugs = int(counts[0][1]) - nbugs
    if deltabugs:
        bugsign = (deltabugs < 0) and "-" or "+"
        deltabugs = " (%s%d)" % (bugsign, abs(deltabugs))
    else:
        deltabugs = " (no change)"

    deltapatches = int(counts[1][1]) - npatches
    if deltapatches:
        patchsign = (deltapatches < 0) and "-" or "+"
        deltapatches = " (%s%d)" % (patchsign, abs(deltapatches))
    else:
        deltapatches = " (no change)"

    print
    print "Bug/Patch Summary"
    print "-----------------"
    print
    print "%s open / %s total %s%s" % (counts[0][1],counts[0][2],
                                       counts[0][0].lower(),deltabugs)
    print "%s open / %s total %s%s" % (counts[1][1],counts[1][2],
                                       counts[1][0].lower(),deltapatches)

    current = get_current_from_sf(bugurlfmt)
    local = get_local_from_db("openbugs")
    newbugs, closedbugs, continuingbugs = compute_changes(current, local)

    current = get_current_from_sf(patchurlfmt)
    local = get_local_from_db("openpatches")
    newpatches, closedpatches, continuingpatches = compute_changes(current, local)

    print_summary(newbugs, "New Bugs", detailfmt)
    print_summary(newpatches, "New Patches", detailfmt)

    print_summary(closedbugs, "Closed Bugs", detailfmt)
    print_summary(closedpatches, "Closed Patches", detailfmt)

    update_local(newbugs, closedbugs, continuingbugs, "openbugs")
    update_local(newpatches, closedpatches, continuingpatches, "openpatches")



    ###### patches ######
        

if __name__ == "__main__":
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    import os
    sys.stdout = StringIO.StringIO()
    try:
        main()
        output = sys.stdout.getvalue()
    except:
        output = ""
    if output:
        pipe = os.popen('mail -s "Weekly Python Bug/Patch Summary"'
                        '  python-dev@python.org,T.A.Meyer@massey.ac.nz', 'w')
        pipe.write(output)
