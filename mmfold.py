#!/usr/bin/env python

"""
Generate brief summary of all pending administrative messages for a mailing
list managed by Mailman 2.1.

Usage: Run this script with the URL (with or without password info) for the
admindb page on the command line.  If you don't provide the password (a
query string of the form '?admpw=PASSWORD' you will be prompted for the
password.  The url will be fetched then massaged into a more compact form
and sent to your web browser.  To process held messages for a bunch of
mailing lists I define a shell function like this:

function mmcheck {
    for url in \
        http://SOME.SERVER/mailman/admindb/SOMELIST?admpw=PASSWORD1 \
        http://SOME.SERVER/mailman/admindb/SOMEOTHERLIST?admpw=PASSWORD2 \
        ...
    ; do
        python mmfold.py $url
    done
}
"""

import sys
import urllib
import re
import webbrowser
import os
import getpass
import tempfile
import time
import urlparse

def brief(reason):
    if reason.startswith("Post by non-member"):
        return "non-member post"
    if reason.startswith("Message body is too big"):
        return "too big"
    if reason == "Message has a suspicious header":
        return "probably spam"
    if reason == "Message has implicit destination":
        return "implicit destination"
    return reason

def main():
    try:
        url = sys.argv[1]
    except IndexError:
        print "must specify url to fetch"
        return 1

    sawsub = False
    sawreason = False
    sawsender = False
    emitted = False
    sub = ""
    msgurl = ""
    sender = ""

    x = urlparse.urlparse(url)
    query = []
    passwd = ""
    lst = x.path.split("/")[-1]
    for keyval in x.query.split("&"):
        try:
            key, val = keyval.split("=")
        except ValueError:
            query.append(keyval)
        else:
            if key == "admpw":
                passwd = val
            else:
                query.append(keyval)
    if not passwd:
        passwd = getpass.getpass(prompt="%s password: " % lst)
    query = "&".join(query)
    url = urlparse.urlunparse((x.scheme, x.netloc, x.path, x.params,
                               query, x.fragment))

    htmlfile = os.path.join(tempfile.gettempdir(), "mmhelp-%s.html" % lst)
    sys.stdout = open(htmlfile, "w")

    try:
        print '''<h1 align="center">Mailman Review Page (%s)</h1>''' % lst
        print '''<center>'''
        print '''<form action="%s" method="POST">''' % url
        print '''<input type="hidden" name="adminpw" value="%s">''' % passwd
        print '''<table border="1" cellpadding="2" cellspacing="0">'''
        print "<tr>"
        print "<th>Def</th><th>Acc</th><th>Rej</th><th>Disc</th>"
        print "<th>Subject</th><th>Sender</th><th>Reason</th>"
        print "</tr>"
        lines = []
        for line in urllib.urlopen(url+"?adminpw=%s" % passwd):
            line = line.strip()
            if sawsub:
                sub = re.sub("</?td>", "", line).strip()
                if not sub:
                    sub = "<no subject>"
                sawsub = False
                continue

            if sawreason:
                reason = re.sub("</?td>", "", line)
                if not reason:
                    reason = "<no reason>"
                reason = brief(reason)
                sawreason = False

                msgid = msgurl.split("?msgid=")[1]
                # comment is just so the lines sort properly by subject
                # need to replace % by %% because the resulting line
                # will be the lhs of a string formatting expression later
                out = ['''<!-- %s --><tr bgcolor="%%s">''' %
                       sub.replace("%", "%%")]
                for i in range(4):
                    if i == 3: checked = " CHECKED"
                    else: checked = ""
                    out.append('''<td><input name="%s" type="radio" value="%d"%s></td>''' %
                               (msgid, i, checked))
                out.append('''<td><font size="-1"><a href="%s&adminpw=%s">%s</a></font></td>'''
                           '''<td><font size="-1">%s</font></td>'''
                           '''<td><font size="-1">%s</font></td>''' %
                           (msgurl,
                            passwd.replace("%", "%%"),
                            sub.replace("%", "%%"),
                            sender.replace("%", "%%"),
                            reason))
                out.append("</tr>")
                lines.append("".join(out))
                continue

            mat = re.search('''<a href="([^"]+)">\[[0-9]+\]''', line)
            if mat is not None:
                msgurl = mat.group(1)
                continue

            mat = re.search('''>Subject:<''', line)
            if mat is not None:
                sawsub = True
                continue

            mat = re.search('''>Reason:<''', line)
            if mat is not None:
                sawreason = True
                continue

            mat = re.search('''>From:<''', line)
            if mat is not None:
                sender = re.sub("<[^>]+>", "", line)
                if not sender:
                    sender = "<sender unknown>"
                sender = sender.replace("From:", "")
                continue

        lines.sort()
        colors = {True: "#ccccdd", False: "white"}
        cindx = True
        for line in lines:
            color = colors[cindx]
            cindx = not cindx
            print line % color
        print "</table>"
        print '''<input name="submit" type="SUBMIT" value="Submit All Data">'''
        print "</form>"
        print '''</center>'''
    finally:
        sys.stdout.close()
        sys.stdout = sys.__stdout__

    if lines:
        webbrowser.open("file:///" + htmlfile)
        print >> sys.stderr, len(lines), "items sent to browser for review"
    else:
        print >> sys.stderr, "no messages await review for", lst
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
