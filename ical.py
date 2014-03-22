#!/usr/bin/env /usr/local/bin/pythonw

"""
%(prog)s - add or print iCal events or todos from the command line

Usage
-----

%(prog)s [ -E ] [ -a | -p ] [ -e | -t ] [ -c Calendar ] [ args ... ]

    -a - add a todo or an event (default)
    -p - print todos or events
    -e - add or print events (default)
    -t - add or print todos
    -c Calendar - specify calendar to operate on (default: Home)
    -E - get args from email message on stdin
    -h - print this help and exit
    args - words or key=value pairs that are used to fill in fields when
           creating todos or events.  If args are given when printing,
           an error is raised.  Which keys have meaning depend on the
           action.  When adding events, the keys understood are start,
           end, summary, description, url and location.  When adding
           todos, the keys understood are due, summary, url and
           priority.  Words that aren't part of key=value pairs are
           accumulated into a 'text' key and used as the description if
           none is given.

Dates can be in a wide variety of formats thanks to the date parser in
the dateutils package.  One extension: 'today' and 'tomorrow' are
recognized at the start of a date/time string.

Examples
--------

    %(prog)s -t -a due=2006-02-21 another release
        Add a todo with a due date of February 21, 2006 and a summary of
        'another release'.

    %(prog)s -a start=2006-02-13T13:00 description='Ellen returns'
        Add an event with a start date/time of 1pm on February 13, 2006
        and a description of 'Ellen returns'.

    %(prog)s -p -t
        Print all todos.

    %(prog)s -p
        Print all events that have not expired.

Email use
---------

If you feed an email message to %(prog)s -E on stdin, it will parse
the key=value pairs from the text/plain parts of the message.  The
subject, minus a possible leading 'ical events' or 'ical todo' prefix,
is used as the summary.  Any lines in the parsed text/plain parts that
aren't key=value pairs are used as the description.  I use it via
procmail with recipes like these:

    :0:ical.lock
    * ^Subject: ical todo
    | %(prog)s -E -a -t

    :0:ical.lock
    * ^Subject: ical event
    | %(prog)s -E -a -e
"""

import sys
import os
import getopt
import datetime
import StringIO
import email.Parser

import dateutil.parser

from appscript import *

prog = os.path.split(sys.argv[0])[1]

TODAY = datetime.datetime.now().date()
TOMORROW = TODAY + datetime.timedelta(days=1)

PRIORITIES = {
    k.no_priority: "",
    k.high_priority: "high",
    k.medium_priority: "medium",
    k.low_priority: "low",
    }

def fmt_date(dt):
    "Format a datetime object with special attention for today and tomorrow."
    if dt.date() > TOMORROW:
        s = dt.strftime("%Y-%m-%d")
    elif dt.date() > TODAY:
        s = "tomorrow"
    else:
        s = "today"
    s += " " + dt.strftime("%I:%M%p")
    return s
    
def fmt_date_range(st, en):
    "Format a pair of datetime objects."
    date = fmt_date(st)
    if en > st:
        if en.date() > st.date():
            if en.date() > TOMORROW:
                date += " " + en.strftime("%Y-%m-%d")
            else:
                date += " tomorrow"
        date += " " + en.strftime("%I:%M%p")
    return date

def print_cal(what, calendar):
    "Print events or todos from the given calendar."
    if what == "event":
        ev = app('iCal').calendars.filter(its.title == calendar).events
        events = zip(ev.start_date.get(), ev.end_date.get(), 
                     ev.summary.get(), ev.description.get())
        events.sort()
        for st, en, summ, descr in events:
            if st.date() < TODAY:
                continue
            print fmt_date_range(st, en),
            if summ:
                print ":", summ,
            print
            if descr != k.MissingValue:
                for line in descr.split("\n"):
                    print " ", line.strip()
    elif what == "todo":
        to = app('iCal').calendars.filter(its.title == calendar).todos
        # This sorting weirdness is because datetime objects and
        # k.MissingValue objects can't be compared.
        todos = zip(to.due_date.get(),
                    to.priority.get(),
                    to.summary.get(),
                    to.description.get(),
                    to.completion_date.get())
        todos_dates = [(dt,p,s,d,c) for (dt,p,s,d,c) in todos
                                      if dt != k.MissingValue]
        todos_dates.sort()
        todos_nodates = [(dt,p,s,d,c) for (dt,p,s,d,c) in todos
                                        if dt == k.MissingValue]
        todos_nodates.sort()
        todos = todos_dates + todos_nodates

        for (dt,p,s,d,c) in todos:
            if c != k.MissingValue and c.date() <= TODAY:
                continue
            if dt == k.MissingValue:
                dt = ""
            else:
                dt = "%s, " % fmt_date(dt)
            p = PRIORITIES.get(p, "")
            p = p and "%s: " % p or ""
            print "%(dt)s%(p)s%(s)s" % locals()
            if d != k.MissingValue:
                for line in d.split("\n"):
                    print " ", line.strip()

def add_item(what, calendar, **kwds):
    "Add an event or a todo to the given calendar."
    text = kwds.get("text", "")
    if what == "event":
        start = parse_date(kwds.get("start", "today"))
        # default end time to one hour after start time
        end = kwds.get("end")
        if end is None:
            end = start + datetime.timedelta(hours=1)
        else:
            end = parse_date(end)

        app('iCal').calendars.filter(its.title==calendar).events.end.make(
            new=k.event, with_properties={
            k.start_date: start,
            k.end_date: end,
            k.summary: kwds.get("summary", ""),
            k.description: kwds.get("description", text),
            k.url: kwds.get("url", ""),
            k.location: kwds.get("location", "")})

    elif what == "todo":
        due = kwds.get("due", k.MissingValue)
        if due != k.MissingValue:
            due = parse_date(due)
        app('iCal').calendars.filter(its.title == calendar).todos.end.make(
            new=k.todo, with_properties={
            k.summary: kwds.get("summary", ""),
            k.url: kwds.get("url", ""),
            k.due_date: due,
            k.description: kwds.get("description", text),
            k.priority: int(kwds.get("priority", 0))})

def parse_date(dt):
    "Parse a date/time string, treating 'today' and 'tomorrow' specially."
    dt = dt.lower()
    if dt.startswith("today"):
        dt = dt.replace("today", str(TODAY))
    elif dt.startswith("tomorrow"):
        dt = dt.replace("tomorrow", str(TOMORROW))
    return dateutil.parser.parse(dt)

def usage(msg=""):
    if msg:
        print >> sys.stderr, msg
        print >> sys.stderr
    print >> sys.stderr, __doc__.strip() % globals()

def get_args_from_email():
    "Get event/todo args from an email message (say, for use w/ procmail)"

    # Standard input is an email message with the item summary in the
    # subject (possibly beginning with "ical event" or "ical todo") and
    # key=value pairs in the text/plain parts of the body. Lines that aren't
    # in key=value format are treated as the description.  Parsing ends with
    # the first line that equals "--" (typically the start of the
    # signature).
    msg = email.Parser.Parser().parse(sys.stdin)
    kwds = {}
    swords = msg.get("Subject", "").split()
    if [s.lower() for s in swords[0:2]] in [["ical", "event"],
                                            ["ical", "todo"]]:
        del swords[0:2]
    kwds["summary"] = " ".join(swords)

    text = []
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            for line in part.get_payload().split("\n"):
                if line.strip() == "--":
                    break
                try:
                    key, val = line.strip().split("=", 1)
                except ValueError:
                    text.append(line)
                else:
                    kwds[key] = val
    if text:
        kwds["description"] = "\n".join(text).strip()
    return kwds

def get_args_from_cmdline(args):
    kwds = {}
    text = []
    for arg in args:
        try:
            key, val = arg.split("=", 1)
        except ValueError:
            text.append(arg)
        else:
            kwds[key] = val
    if text:
        if "text" in kwds:
            raise ValueError, "multiple text sources"
        kwds["text"] = " ".join(text)
    return kwds

def main(args):
    opts, args = getopt.getopt(args, "apetc:hE",
                               ["add", "print", "event", "todo",
                                "calendar=", "help", "email"])
    action = "add"
    what = "event"
    calendar = "Home"
    email = False
    for opt, arg in opts:
        if opt in ("-p", "--print"):
            action = "print"
        elif opt in ("-e", "--event"):
            what = "event"
        elif opt in ("-a", "--add"):
            action = "add"
        elif opt in ("-t", "--todo"):
            what = "todo"
        elif opt in ("-c", "--calendar"):
            calendar = arg
        elif opt in ("-E", "--email"):
            email = True
        elif opt in ("-h", "--help"):
            usage("help for %(prog)s" % globals())
            return 0

    if email:
        kwds = get_args_from_email()
    else:
        kwds = get_args_from_cmdline(args)

    if action != "add" and kwds:
        usage("keywords given with %s action" % what)
        return 1

    if action == "add":
        add_item(what, calendar, **kwds)
    elif action == "print":
        print_cal(what, calendar)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
