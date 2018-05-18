#!/usr/bin/env python

# watch.py - keep an eye on the display and tell the user when to rest
# Author: Skip Montanaro (skip.montanaro@gmail.com)
# $Id: watch.py,v 1.12 2002/12/14 18:13:17 montanaro Exp $
# project home - http://sourceforge.net/projects/watch/
"""Usage: {PROG} [ args ]
Command line arguments:

    short       long            meaning                      default
    -----       ----            -------                      -------
     -h         --help          display this help            n/a
     -w n       --work=n        set work time in minutes     {WORK_TM}
     -r n       --rest=n        set rest time in minutes     {REST_TM}
     -s name    --server=name   set server host              localhost
     -p n       --port=n        set server port              8080
     -g gspec   --geometry=g    set startup geometry         sys-dependent
     -n         --noserver      don't contact or start server
     -m mode    --mode=mode     fascist or friendly

Watch is a Tk-based program that monitors work and rest times for keyboard
and mouse use to help users avoid overuse that can lead to or exacerbate
repetitive strain injuries.  The user can define the duration of work and
rest intervals.  In fascist mode, the user can't override the displayed rest
window.  In friendly mode, a cancel button is available to allow the user to
prematurely terminate the rest interval.

Watch currently runs on Linux, Windows and MacOSX systems as long as tkinter
is available.  It's never been tried on MacOS 9, but there isn't any
insurmountable reason why it can't be made to work there either.

Depending on the platform, activity of the mouse and possibly the keyboard
is tracked.  Mouse position can be determined via Tk, but monitoring
keyboard activity is not currently possible in a platform-independent way.

How effectively Watch prevents you from working is subject to the properties
of the system in use.  On Windows and Macintosh systems it's likely that you
will always be able to get at the toolbar.  On X-based systems it's more
likely that Watch can completely obscure all points of interaction on the
screen.

Watch allows multiple instances to coordinate their efforts via a small
XML-RPC server.  This is a useful feature if you are cursed with multiple
computers in your cubicle.  When started, Watch will try to contact a
running server.  You can tell Watch where the server is or how it should be
started using the -s (or --server=) and -p (or --port=) command line
arguments.  If it is unable to contact an existing server it will try to
start one up itself.  If that fails, it will operate independently.  If the
-n (or --noserver) command line arg is given, Watch will not attempt to
contact or start a watch-server instance.  Note: spawning and killing the
server may not work properly on non-Unix systems.

If no direct detection of keyboard activity is possible on your platform but
you have Emacs available, you can define a function to jiggle the mouse and
bind it to the auto-save-hook and after-save-hook.  This allows the typing
watcher to notice the activity.  It toggles the jiggle direction so that the
next time it jiggles the mouse the other way.  The following code uses
mouse-pixel-position and set-mouse-pixel-position.  I'm not sure if they are
in FSF Emacs.  They are certainly in XEmacs from at least version 20.3.

    (setq pointer-jiggle-val 3)
    (defun jiggle-mouse ()
      (if window-system
          (progn
            (let ((pos (mouse-pixel-position))
                  win x y)
              (setq win (car pos))
              (if (and (not (eq win nil)) (not (eq '(nil) (cdr pos))))
                  (progn
                    (setq x (car (cdr pos)))
                    (setq y (cdr (cdr pos)))
                    (set-mouse-pixel-position win (+ pointer-jiggle-val x) y)
                    (setq pointer-jiggle-val (* -1 pointer-jiggle-val))))))))

    (setq auto-save-hook '(jiggle-mouse))
    (setq after-save-hook '(jiggle-mouse))

Author: Skip Montanaro (skip.montanaro@gmail.com)
Project Home: https://github.com/smontanaro/python-bits/
"""

# My logic is all screwed up, I think. At the start of a work interval, we
# know the following:

# * work and rest intervals in minutes
# * start time
# * end of work time (start time + work interval)
# * end of rest time (start time + work interval + rest interval)

# Assuming the user doesn't mess with the scales, when the current time
# exceeds the end of work time, we move from work to rest. When the current
# time exceeds the end of the rest time, we start all over again.

# Things we (s)upport (or (w)ant to support):

# (s) manipulation of the work and rest sliders by the user
# (s) termination of work period (press Rest button)
# (s) termination of rest period (press Cancel button in friendly mode)
# (s) exchange of work/rest details with other cooperating instances
# (w) note beginning of idle time when laptop lid closes, resumption
#     of work time when lid reopens
# (w) extend end of work time by one minute for every minute of idle time
#     up to the length of the work interval
# (w) add one second of rest time every time mouse/keyboard activity is
#     detected when the user is supposed to be resting

from __future__ import print_function

import atexit
import datetime
import getopt
import logging
import os
import signal
import socket
import sys
import time

from six.moves.tkinter import (Toplevel, Canvas, Frame, Scale, Radiobutton, Button,
                               Scrollbar, StringVar, Label, Text, Tk,
                               RIGHT, LEFT, BOTH, HORIZONTAL, Y, NORMAL, END,
                               ACTIVE, DISABLED)
from six.moves import xmlrpc_client

from watch import collector

LID_STATE = "/proc/acpi/button/lid/LID0/state"

CHK_INT = 1000                  # milliseconds
WORK_TM = 10
REST_TM = 3

PORT = 8080
HOST = "localhost"
FORMAT = '{asctime} {levelname} {message}'
PROG = os.path.split(sys.argv[0])[-1]


### dialog support class adapted from Fredrik Lundh's Tkinter docs
class Dialog(Toplevel):
    def __init__(self, parent, title=None, content=""):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        self.log = logging.getLogger(__name__)

        if title:
            self.title(title)

        self.parent = parent
        self.body = Frame(self)
        self.fill_body(content)
        self.body.pack(padx=5, pady=5)

        self.create_buttonbox()

        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.ok)

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))

        self.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def fill_body(self, content):
        scrollbar = Scrollbar(self.body)
        scrollbar.pack(side=RIGHT, fill=Y)

        text = Text(self.body, yscrollcommand=scrollbar.set)
        text.pack(side=LEFT, fill=BOTH)
        text.config(state=NORMAL)
        text.delete(1.0, END)
        text.insert(END, content)
        text.config(state=DISABLED)

        scrollbar.config(command=text.yview)

    def create_buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("&<Return>", self.ok)
        self.bind("&<Escape>", self.ok)

        box.pack()

    def ok(self, _event=None):
        self.withdraw()
        self.update_idletasks()
        self.parent.focus_set()
        self.destroy()


class Meter(Canvas):
    """Progress meter widget.

    Adds two options to its Canvas base class, min and max, which define
    the start and end values of the meter.  The set_range
    method can be used as well.  The set method is used by the caller
    to define the actual progress from min to max.

    If the width, height or background options are not specified, they
    default to 100, 10, and black, respectively. If given, the converter
    must specify a three-argument function(min, value, max) which computes
    this relation:

    (value - min) / (max - min)

    returning a float between 0.0 and 1.0.
    """

    def __init__(self, master=None, min_val=0, max_val=100, converter=None,
                 **kw):
        self.log = logging.getLogger(__name__)
        self.min_val = min_val
        self.max_val = max_val
        self.converter = converter
        kw['width'] = kw.get('width', 100)
        kw['height'] = kw.get('height', 10)
        kw['background'] = kw.get('background', "black")
        self.rect = None
        Canvas.__init__(*(self, master), **kw)

    def set_range(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
        # Special case - using datetime objects for the bounds and values on
        # Python2, which doesn't support division of timedelta objects.
        if (self.converter is None and
            sys.version_info.major < 3 and
            isinstance(min_val, datetime.datetime)):
            self.converter = self._td_divider

    # pylint: disable=no-self-use
    def _td_divider(self, min_val, value, max_val):
        "Perform the progress calculation for timedelta objs on Py2."
        num = (value - min_val).total_seconds()
        den = (max_val - min_val).total_seconds()
        return num / den

    def set(self, value):
        "Note progress from min to value"
        if self.rect is not None:
            self.delete(self.rect)
        metheight = int(self.cget("height")) + 1
        canwidth = int(self.cget("width"))
        if self.converter is not None:
            progress = self.converter(self.min_val, value, self.max_val)
        else:
            progress = (value - self.min_val) / (self.max_val - self.min_val)
        metwidth = canwidth * progress
        self.rect = self.create_rectangle(
            0, 0, metwidth, metheight, outline="red", fill="red")
        self.update()

    def reset(self):
        self.set(self.min_val)


class Task(Frame):
    def __init__(self,
                 master=None,
                 work=WORK_TM,
                 rest=REST_TM,
                 server=HOST,
                 port=PORT,
                 mode='fascist'):
        """create the task widget and get things started"""

        self.lid_state = "open"
        self.lid_time = time.time()
        self.interrupt_count = 0
        self.then = 0.0
        self.old_work = 0.0
        self.state = "working"
        self.cancel_rest = 0

        self.log = logging.getLogger(__name__)

        Frame.__init__(*(self, master))

        self.mode = StringVar()
        self.mode.set(mode)    # "fascist" or "friendly"

        # create main interactor window
        self.workmeter = Meter(self, background="grey50")
        self.workmeter.pack()

        self.work_frame = Frame(self)
        self.work_frame.pack()
        self.work_label = Label(self.work_frame, text="Work time:")
        self.work_label.pack(side=LEFT)
        self.work_scl = Scale(
            self.work_frame,
            orient=HORIZONTAL,
            from_=1,
            to=max(45, work),
            command=self.reset_duration)
        self.work_scl.set(work)
        self.work_scl.pack(side=LEFT)

        self.rest_frame = Frame(self)
        self.rest_frame.pack()
        self.rest_label = Label(self.rest_frame, text="Rest time:")
        self.rest_label.pack(side=LEFT)
        self.rest_scl = Scale(
            self.rest_frame,
            orient=HORIZONTAL,
            from_=1,
            to=max(15, rest),
            command=self.reset_duration)
        self.rest_scl.set(rest)
        self.rest_scl.pack(side=LEFT)

        self.radio_frame = Frame(self)
        self.radio_frame.pack()
        self.dictator = Radiobutton(
            self.radio_frame,
            text="Fascist",
            variable=self.mode,
            value="fascist")
        self.friend = Radiobutton(
            self.radio_frame,
            text="Friendly",
            variable=self.mode,
            value="friendly")
        self.dictator.pack(side=LEFT)
        self.friend.pack(side=LEFT)

        self.button_frame = Frame(self)
        self.button_frame.pack()
        self.restb = Button(self.button_frame, text="Rest", command=self.rest)
        self.restb.pack(side=LEFT)
        self.stopb = Button(self.button_frame, text="Quit", command=self.quit)
        self.stopb.pack(side=LEFT)
        self.helpb = Button(self.button_frame, text="Help", command=self.help)
        self.helpb.pack(side=LEFT)

        # create the cover window
        self.cover = Toplevel(background="black")
        self.cover.withdraw()
        # user can't resize it
        self.cover.resizable(0, 0)
        # when displayed, it should cover all displays
        (w, h) = (self.winfo_vrootwidth(), self.winfo_vrootheight())
        if self.log.getEffectiveLevel() <= logging.DEBUG:
            # but we reduce it while debugging
            w, h = (w / 5, h / 5)
        self.cover.geometry("%dx%d+0+0" % (w, h))

        # and it's undecorated
        self.cover.overrideredirect(1)

        # cover contains a frame with rest message and meter
        f = Frame(self.cover, background="black")
        self.restnote = Label(f, background="black", foreground="white")
        self.restmeter = Meter(f, background="grey50", height=10, width=200)
        self.restnote.pack(pady=2)
        self.restmeter.pack(fill="x", expand=1, pady=2)
        self.cancel_button = Button(f, text="Cancel Rest", command=self.cancel)
        f.pack()

        # used by the default activity checker
        self.mouse = None

        self.setup_server(server, port)

        # self.last_int is the last time the server was alerted to activity
        # self.now is the server's notion of the current time
        # idle time is therefore max(0, self.now-self.last_int)
        (self.last_int, _w_time, _r_time, self.now) = self.server.get()
        self.idle = max(0, self.now - self.last_int)

        self.bgcolor = self["background"]

        # start the ball rolling
        self.after(CHK_INT, self.tick)
        self.work()

    def setup_server(self, server, port):
        if server is None:
            self.server = collector.Collector()
            self.log.debug("using private Collector()")
            return

        self.server = xmlrpc_client.ServerProxy("http://%s:%d" % (server,
                                                                  port))
        try:
            self.server.get()
            self.log.debug("found existing server")
        except socket.error:
            if server in ["", "localhost", "127.0.0.1"]:
                cmd = "watch-server.py"
                args = ["-p", "%d" % port]
                pid = os.spawnvp(os.P_NOWAIT, cmd, args)
                # wait briefly for server to start
                time.sleep(0.2)
                self.server = xmlrpc_client.ServerProxy(
                    "http://%s:%d" % (server, port),
                    allow_none=True)
                # try connecting
                for _i in range(10):
                    try:
                        self.server.get()
                        atexit.register(os.kill, pid, signal.SIGHUP)
                        self.log.debug("spawned server")
                        return
                    except socket.error:
                        time.sleep(0.1)
            # nothing else worked, so fall back to an embedded collector
            self.server = collector.Collector()
            self.log.debug("using private Collector()")

    def reset_duration(self, _dummy=None):
        """reset work/rest interval lengths to current scale values"""
        wtime = self.work_scl.get()
        self.workmeter.set_range(self.workmeter.min_val,
                                 self.workmeter.min_val + wtime * 60)
        self.restmeter.set_range(self.restmeter.min_val,
                                 self.restmeter.min_val +
                                 self.rest_scl.get() * 60)
        # only time the user can fiddle the work/rest meters is during
        # the work phase, so the only scale change that matters for extending
        # or contracting the end of the interval is the work scale
        try:
            delta = wtime - self.old_work
        except AttributeError:
            delta = 0
        self.log.debug(__("then: {} delta: {}m", hhmm(self.then), delta))
        self.then = self.then + delta * 60
        self.old_work = wtime

        self.server.put(self.work_scl.get(), self.rest_scl.get())

    def work(self):
        """start the work period"""
        self.reset_warning()
        self.restmeter.reset()
        self.state = "working"
        self.then = self.now + self.work_scl.get() * 60
        self.log.debug(__("work: then: {}", hhmm(self.then)))
        self.workmeter.set_range(self.now, self.then)
        self.workmeter.reset()
        self.cover.withdraw()

    def warn_work_end(self):
        """alert user that work period is almost up"""
        self.set_background("yellow")

    def reset_warning(self):
        """back to plain old grey bg"""
        self.set_background(self.bgcolor)

    def set_background(self, color):
        for w in (self, self.work_scl, self.rest_scl, self.dictator,
                  self.friend, self.button_frame, self.stopb, self.restb,
                  self.helpb, self.work_frame, self.rest_frame,
                  self.radio_frame, self.work_label, self.rest_label):
            w["background"] = color

    def rest(self):
        """overlay the screen with a window, preventing typing"""
        self.cancel_rest = 0
        self.workmeter.reset()
        self.state = "resting"
        # the user may not have been typing or mousing right up to the
        # work/rest threshold - give credit for whatever rest time has
        # already been accumulated
        resttime = self.rest_scl.get() * 60 - (self.now - self.last_int)
        if resttime < 0:
            self.cancel()
            self.work()
            return
        mins, secs = divmod(resttime, 60)
        self.then = self.now + resttime
        self.cover.deiconify()
        self.cover.tkraise()
        resttext = ("Rest for %dm%02ds please..." % (mins, secs))
        self.restnote.configure(text=resttext)
        self.restmeter.set_range(self.now, self.then)
        self.restmeter.reset()
        if self.mode.get() == "friendly":
            self.cancel_button.pack(pady=2)
        else:
            self.cancel_button.pack_forget()

        self.log.debug(__("rest: state: {} now: {} then: {} active? {}",
                          self.state, hhmm(self.now), hhmm(self.then),
                          self.check_activity()))

    def help(self):
        Dialog(self.master, title="Help", content=usageText())

    ### ---- define activity checkers here ---- ###
    # keyed by sys.platform or "default" to return a method that checks
    # for mouse/keyboard activity
    _dispatch = {}

    def check_activity(self):
        """check mouse/keyboard activity info

        where possible, call platform-dependent routine to get mouse and
        keyboard info, otherwise, just return mouse info

        in all cases, the value returned should evaluate to False if no
        activity was detected.
        """
        active = False
        if self.lid_state == "open":
            dflt = self._dispatch["default"]
            checker = self._dispatch.get(sys.platform, dflt)
            active = checker(self)
            if active:
                self.server.tick()
        return active

    def check_mouse(self):
        """default checker, just compares current w/ saved mouse pos"""
        mouse = self.winfo_pointerxy()
        try:
            return mouse != self.mouse
        finally:
            self.mouse = mouse

    _dispatch["default"] = check_mouse

    def get_linux_interrupts(self):
        count = 0
        # Can't seem to find mouse interrupts, so for now, just watch
        # keyboard and mix add get_mouseinfo() output as a substitute for
        # mouse interrupts.
        last_count = self.interrupt_count
        for line in open("/proc/interrupts"):
            fields = line.split()
            if fields[0] == "1:":
                count = sum(int(fields[n]) for n in range(1, 8))
                self.interrupt_count = count
                break
        return self.check_mouse() or self.interrupt_count > last_count

    _dispatch["linux"] = get_linux_interrupts

    def check_lid_state(self):
        if os.path.exists(LID_STATE):
            for line in open(LID_STATE):
                fields = line.strip().split()
                if fields[0] == "state:":
                    return self.maybe_change_lid_state(fields[1])
        else:
            self.lid_state = "open"
        return 0

    def maybe_change_lid_state(self, state):
        """Take necessary action when lid state changes.

        Return True if lid state changed.
        """
        idle = 0
        if state != self.lid_state:
            self.log.info(__("lid state changed: {}", state))
            lid_time = time.time()
            if state == "open":
                idle = lid_time - self.lid_time
                self.log.info(__("idle for {}s", idle))
            self.lid_state = state
            self.lid_time = lid_time
        return idle

    def tick(self):
        """perform periodic checks for activity or state switch"""
        # Unlike the gobject.timeout-type functions, Tk's after function
        # needs to be rescheduled after each call.
        self._tick()
        self.after(CHK_INT, self.tick)

    def _tick(self):
        (self.last_int, work_time, rest_time, self.now) = self.server.get()
        # Check for mouse or keyboard activity.  If the lid on a laptop was
        # closed long enough ago, we immediately launch into a new work
        # interval.
        idle_time = self.check_lid_state()
        if idle_time > rest_time * 60:
            self.log.info(__("The lid is up! Back to work: {}", hhmm(idle_time)))
            self.work()
            return

        active = self.check_activity()
        idle = max(0, self.now - self.last_int)

        # Adjust work/rest times if they changed in another
        # watch instance
        if (self.work_scl.get() != work_time or
            self.rest_scl.get() != rest_time):
            self.work_scl.set(work_time)
            self.rest_scl.set(rest_time)

        self.log.debug(__("work: state: {} now: {} then: {} active? {}",
                          self.state, hhmm(self.now), hhmm(self.then),
                          active))
        if self.state == "resting":
            # user explicitly cancelled the rest or the idle period
            # exceeded the desired rest time
            if self.cancel_rest or idle > rest_time * 60:
                self.work()
                return

            # make sure the rest window is as far up the window stack as
            # possible
            self.cover.tkraise()

            if idle <= self.idle:
                # user moved something - extend rest by a second
                self.then += 1
                self.restmeter.set_range(self.restmeter.min_val, self.then)
                self.restmeter.set(self.now)
                self.idle = idle

            # update message to reflect rest time remaining
            timeleft = int(round(self.then - self.now))
            minleft, secleft = divmod(timeleft, 60)
            resttext = ("Rest for %dm%02ds please..." % (
                minleft, secleft))
            self.restnote.configure(text=resttext)

        else:
            # if it's been at least the length of the rest interval
            # since last interrupt, reset the work interval
            if idle >= rest_time * 60:
                self.work()
                return

            self.idle = idle

            if self.now > self.then:
                # work period expired
                self.rest()
                return

            if self.now + 60 > self.then:
                # work period nearly expired - warn user
                self.warn_work_end()
            else:
                self.reset_warning()

        self.restmeter.set(self.now)
        self.workmeter.set(self.now)

    def cancel(self):
        self.cancel_rest = 1

# pylint: disable=too-few-public-methods
class BraceMessage:
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)
__ = BraceMessage

def hhmm(t):
    return datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")

def main(args):
    (work, rest, geometry, debug, server, port, mode) = parse(args)
    logging.basicConfig(level="DEBUG" if debug else "INFO", style='{',
                        format=FORMAT)
    app = Tk()
    app.title("Typing Watcher")
    if geometry:
        app.geometry(geometry)
    task = Task(
        master=app,
        work=work,
        rest=rest,
        server=server,
        port=port,
        mode=mode)
    task.pack()
    app.mainloop()


def usage():
    print(usageText(), file=sys.stderr)
    sys.exit()


def usageText():
    return __doc__.format(**globals())


def parse(args):
    opts, args = getopt.getopt(args, "ndhw:r:g:s:p:m:", [
        'debug', 'help', 'noserver', 'server=', 'port=', 'work=', 'rest=',
        'geometry=', 'mode='
    ])

    # defaults
    work = 20
    rest = 3
    geometry = ""
    debug = 0
    server = "localhost"
    port = 8080
    mode = 'fascist'

    for opt, val in opts:
        if opt in ['-h', '--help']:
            usage()
        elif opt in ['-d', '--debug']:
            debug = 1
        elif opt in ['-w', '--work']:
            work = int(val)
        elif opt in ['-r', '--rest']:
            rest = int(val)
        elif opt in ['-g', '--geometry']:
            geometry = val
        elif opt in ['-s', '--server']:
            server = val
        elif opt in ['-p', '--port']:
            port = int(val)
        elif opt in ['-n', '--noserver']:
            port = server = None
        elif opt in ['-m', '--mode']:
            mode = val

    if rest > work:
        usage()

    return (work, rest, geometry, debug, server, port, mode)


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit()
