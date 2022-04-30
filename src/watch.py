#!/usr/bin/env python3

# watch.py - keep an eye on the display and tell the user when to
# rest
# Author: Skip Montanaro (skip.montanaro@gmail.com)
# $Id: watch.py,v 1.5 2000/06/18 03:42:24 skip Exp $

# Updated for Python 3 2018/04/26
"""Usage: {PROG} [ --work=min ] [ --rest=min ] [-g geometry ] [ -h ] \\
                 [ --control=style ] [ --loglevel=LEVEL ]

--work=minutes - set work time in minutes (default: {WORK_TM})
--rest=minutes - set rest time in minutes (default: {REST_TM})
--geometry=geo - geometry in typical X fashion
--control=X    - set initial control style to X (fascist or friendly)
--loglevel     - set log level (default {LOG_LEVEL})

Watch is a Tk-based program that monitors work and rest times for keyboard
and mouse use to help users avoid overuse that can lead to or exacerbate
repetitive strain injuries.  The user can define the duration of work and
rest intervals.  In fascist mode, the user can't override the displayed rest
window.  In friendly mode, a cancel button is available to allow the user to
prematurely terminate the rest interval. The user interface includes a rest
button to allow the user to terminate the current work interval.

Activity of the mouse and keyboard is tracked using pynput. I have no
idea how platform-independent that is. At the moment, my only platform
is XUbuntu running Xorg.

"""

import argparse
import asyncio
import datetime
import enum
import logging
import os
import re
import subprocess               # nosec
import sys
import tempfile
import time
from tkinter import (Canvas, Frame, StringVar, Label, Scale, Radiobutton,
                     Button, Tk, Toplevel, LEFT, HORIZONTAL, simpledialog)

import dateutil.parser
import pynput

SUSP_FILE = os.path.join(tempfile.gettempdir(), "suspensions")

START = datetime.datetime.now(tz=datetime.timezone.utc)
EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
ONE_MINUTE = datetime.timedelta(seconds=60)
ONE_SECOND = datetime.timedelta(seconds=1)
ZERO_SECOND = datetime.timedelta(seconds=0)

WORK_TM = 10
REST_TM = 3
LOG_LEVEL = "WARNING"
PROG = os.path.split(sys.argv[0])[-1]

NORMAL = "grey75"
ALERT = "yellow"

TK_SENTINEL_INT = -99999999


class Meter(Canvas):  # pylint: disable=too-many-ancestors
    """Progress meter widget.

    Adds two options to its Canvas base class, min and max, which define
    the start and end values of the meter.  The set_range
    method can be used as well.  The set method is used by the caller
    to define the actual progress from min to max.

    If the width, height or background options are not specified, they
    default to 100, 10, and black, respectively.

    Needs to also have an orientation option.
    """

    def __init__(self, master=None, **kw) -> None:
        self.log = logging.getLogger(__name__)
        self.min = 0
        self.max = 100
        if "min" in kw:
            self.min = kw['min']
            del kw['min']
        if "max" in kw:
            self.max = kw['max']
            del kw['max']

        if "width" not in kw:
            kw['width'] = 100
        if "height" not in kw:
            kw['height'] = 10
        if "background" not in kw:
            kw['background'] = "black"

        self.rect = TK_SENTINEL_INT
        Canvas.__init__(*(self, master), **kw)

    def set_range(self, mn: int, mx: int) -> None:
        self.min = mn
        self.max = mx

    def set(self, value: int) -> None:
        if self.rect != TK_SENTINEL_INT:
            self.delete(self.rect)
        metheight = int(self.cget("height")) + 1
        canwidth = int(self.cget("width"))
        metwidth = canwidth * (value - self.min) / (self.max - self.min)
        self.rect = self.create_rectangle(
            0, 0, metwidth, metheight, outline="red", fill="red")
        self.update()

    def reset(self) -> None:
        self.set(self.min)


LOG = logging.getLogger(__name__)

CHK_INT = 100                   # milliseconds


class wstate(enum.Enum):
    "state of the interface"
    WORKING = "working"
    RESTING = "resting"


class AsyncTk(Tk):
    "Basic Tk with an asyncio-compatible event loop"
    def __init__(self):
        super().__init__()
        self.running = True
        self.runners = [self.tk_loop()]

    async def tk_loop(self):
        "asyncio 'compatible' tk event loop?"
        # Is there a better way to trigger loop exit than using a state vrbl?
        while self.running:
            self.update()
            # obviously, sleep time could be parameterized
            await asyncio.sleep(0.05)

    def stop(self):
        self.running = False

    async def run(self):
        await asyncio.gather(*self.runners)


class SuspendTracker:
    "track most recent wakeup and suspension"
    def __init__(self):
        self.suspend = EPOCH
        self.wake = datetime.datetime.now(tz=datetime.timezone.utc)
        self.tell = 0

    def add_event(self, what, dt):
        "note most recent wake or suspend occurrence"
        attr = "wake" if what == "post" else "suspend"
        setattr(self, attr, dt)

    def check_suspensions(self):
        if self.tell == os.stat(SUSP_FILE).st_size:
            return
        with open(SUSP_FILE, "r", encoding="utf-8") as fobj:
            fobj.seek(self.tell)
            for line in fobj:
                self.tell += len(line)
                LOG.debug("tell: %s, suspension: %r", self.tell, line)
                stamp, what, _action = line.strip().split()
                self.add_event(what, dateutil.parser.parse(stamp))
        LOG.debug("last sleep time: %s", self.last_sleep_length())

    def last_wake(self):
        return self.wake

    def last_sleep_length(self):
        return self.wake - self.suspend


class Task(Frame):  # pylint: disable=too-many-ancestors
    "The base for the entire application"

    def __init__(self, parent=None, work=WORK_TM, rest=REST_TM,
                 control="fascist") -> None:
        """create the task widget and get things started"""

        Frame.__init__(*(self, parent))

        # various inits
        self.parent = parent

        # tick interval - dynamic
        self.tick_int = CHK_INT

        # edges of work and rest intervals
        self.start = now()
        self.switch = self.start + ONE_MINUTE * work
        self.end = self.switch + ONE_MINUTE * rest

        # always begin working
        self.state = wstate.WORKING

        # True if user has been alerted to pending end of work interval
        self.warned = False

        # how long we've been idle, in whole minutes
        self.idle_minutes = ZERO_SECOND

        # initialize interrupt information
        self.last_input_time = now()

        # controlled by fascist/friendly radio buttons
        self.style = StringVar()
        self.style.set(control)

        # create main interactor window

        # progess of current work interval
        self.workmeter = Meter(self, background=NORMAL, height=10, width=200)
        self.workmeter.pack()

        # slider to allow control of work interval length
        f1 = Frame(self)
        f1.pack()
        Label(f1, text="Work time:").pack(side=LEFT)
        self.work_scl = Scale(
            f1,
            orient=HORIZONTAL,
            from_=1,
            to=max(45, work),
            command=self.update_durations)
        self.work_scl.set(work)
        self.work_scl.pack(side=LEFT)

        # slider to allow control of rest interval length
        f2 = Frame(self)
        f2.pack()
        Label(f2, text="Rest time:").pack(side=LEFT)
        self.rest_scl = Scale(
            f2,
            orient=HORIZONTAL,
            from_=1,
            to=max(15, rest),
            command=self.update_durations)
        self.rest_scl.set(rest)
        self.rest_scl.pack(side=LEFT)

        self.create_friendly_control()

        self.create_buttons()

        self.start_listeners()

        # cover window when resting
        self.cover = Toplevel(background="black")
        self.cover.withdraw()
        # user can't resize it
        self.cover.resizable(False, False)
        (w, h) = (self.winfo_screenwidth(), self.winfo_screenheight())
        if logging.getLevelName(LOG.level) == "DEBUG":
            # just a small window when debugging
            (w, h) = (w // 8, h // 8)
        self.cover.geometry(f"{w}x{h}+0+0")

        # and it's undecorated
        self.cover.overrideredirect(True)

        # cover contains a frame with rest message and meter
        f = Frame(self.cover, background="black")
        self.restnote = Label(f, background="black", foreground="white")
        self.restmeter = Meter(f, background=NORMAL, height=10, width=200)
        self.restnote.pack(pady=2)
        self.restmeter.pack(fill="x", expand=1, pady=2)
        self.cancel_button = Button(f, text="Cancel Rest", command=self.work)
        f.pack()

        # start the ball rolling
        self.work()

        # check status every now and then
        self.after(self.tick_int, self.tick)

    def create_friendly_control(self):
        "fascist/friendly control"
        f3 = Frame(self)
        f3.pack()
        Radiobutton(f3, text="Fascist", variable=self.style,
                    value="fascist").pack(side=LEFT)
        Radiobutton(f3, text="Friendly", variable=self.style,
                    value="friendly").pack(side=LEFT)

    def create_buttons(self):
        "GUI's gotta have buttons"
        f4 = Frame(self)
        f4.pack()
        Button(f4, text="Rest", command=self.rest).pack(side=LEFT)
        Button(f4, text="Quit", command=self.parent.stop).pack(side=LEFT)
        Button(f4, text="Help", command=self.help_).pack(side=LEFT)

    def start_listeners(self):
        "listener threads for mouse and keyboard events"
        def handle_input(*_args):
            "handle all keyboard & mouse activity"
            # don't care about the actual events, just update interrupt time
            if self.idle_minutes:
                LOG.info("reset idle minutes counter")
                self.idle_minutes = ZERO_SECOND
            self.last_input_time = now()
            self.reset_tick_interval()

        kb_listen = pynput.keyboard.Listener(on_press=handle_input,
                                             on_release=handle_input)
        kb_listen.daemon = True
        kb_listen.start()
        mouse_listen = pynput.mouse.Listener(on_click=handle_input,
                                             on_scroll=handle_input,
                                             on_move=handle_input)
        mouse_listen.daemon = True
        mouse_listen.start()

    def dt_to_int(self):
        "generate ints needed for bounds of meters"
        start = 0
        switch = int((self.switch - self.start).total_seconds())
        end = int((self.end - self.start).total_seconds())
        now_ = int((now() - self.start).total_seconds())
        return (start, switch, end, now_)

    def refresh_display(self):
        "adjust UI bits"
        start, switch, end, now_ = self.dt_to_int()

        self.workmeter.set_range(start, switch)
        self.restmeter.set_range(switch, end)

        if self.state == wstate.WORKING:
            self.cover.withdraw()
            if self.switch - now() > ONE_MINUTE:
                self.warned = False
            if not self.warned:
                self.set_background(NORMAL)
            self.workmeter.set(now_)
            self.restmeter.set(switch)
        else:
            self.workmeter.set(switch)
            self.restmeter.set(now_)
            self.update_restnote()
            if self.style.get() == "friendly":
                self.cancel_button.pack(pady=2)
            else:
                self.cancel_button.pack_forget()
            self.cover.deiconify()
            self.cover.tkraise()

    def update_restnote(self):
        "update message to reflect rest time remaining"
        timeleft = int(round((self.end - now()).total_seconds()))
        minleft = timeleft // 60
        secleft = timeleft % 60
        msg = f"Rest for {minleft}m{secleft:02d}s please..."
        self.restnote.configure(text=msg)

    def update_durations(self, _dummy=None) -> None:
        """update work/rest interval lengths to current scale values"""
        # all that can change are the ends of the work and rest
        # intervals
        self.switch = self.start + self.work_scl.get() * ONE_MINUTE
        self.end = self.switch + self.rest_scl.get() * ONE_MINUTE

    def work(self) -> None:
        """start the work period"""
        if self.state != wstate.WORKING:
            LOG.info("work: state: %s now: %s end: %s",
                     self.state.value, now().time(), self.switch.time())
        self.state = wstate.WORKING
        self.warned = False
        self.reset_tick_interval()
        self.set_work_bounds(now())

    def rest(self) -> None:
        """overlay the screen with a window, preventing typing"""
        if self.state != wstate.RESTING:
            LOG.info("rest: state: %s now: %s then: %s",
                     self.state.value, self.switch.time(), self.end.time())
        self.state = wstate.RESTING
        self.warned = True
        self.reset_tick_interval()
        self.set_rest_bounds(now())

    def warn_work_end(self) -> None:
        """alert user that work period is almost up"""
        if self.warned:
            return
        # work period nearly expired - warn user
        LOG.debug("Careful pardner, time's almost up.")
        self.warned = True
        self.set_background(ALERT)

    def extend_tick_interval(self):
        "lengthen tick interval up to a max of 5s"
        # work interval can extend for long periods of time during
        # idle periods, so back off when we can.
        self.tick_int = int(min(self.tick_int * 1.3, 5000))

    def reset_tick_interval(self):
        "start over"
        if self.state == wstate.WORKING:
            self.tick_int = CHK_INT
        else:
            # regular tick interval while resting gives more
            # predictable rest note countdown
            self.tick_int = 1000

    def set_background(self, color) -> None:
        def set_bg(w, indent=0):
            for child in w.winfo_children():
                child["background"] = color
                set_bg(child, indent+1)
        self["background"] = color
        set_bg(self)

    def help_(self) -> None:
        d = simpledialog.SimpleDialog(
            self.parent,
            text=usage_text(),
            buttons=["Done"],
            default=0,
            title="Help")
        d.go()

    def tick(self) -> None:
        """perform periodic checks for activity or state switch"""
        LOG.debug("tick, last input @ %s", self.last_input_time.time())

        if self.state == wstate.WORKING:
            self.extend_tick_interval()
            self.work_tick()
        else:
            self.reset_tick_interval()
            self.rest_tick()

        self.refresh_display()
        self.after(self.tick_int, self.tick)

    def work_tick(self):
        now_ = now()

        if now_ - self.last_input_time >= self.idle_minutes + ONE_MINUTE:
            # idle for a(nother) minute, so extend
            self.idle_minutes += ONE_MINUTE
            if self.idle_minutes >= self.switch - self.start:
                LOG.debug("Long idle time - reset work interval")
                self.work()
            else:
                self.increment_bounds(ONE_MINUTE)
                LOG.debug("add a minute to work interval, to %s",
                          self.switch.time())
        elif now_ >= self.end:
            LOG.info("Long suspension - reset work interval")
            self.work()
        elif now_ >= self.switch:
            LOG.debug("time's up!")
            self.rest()
        elif now_ + ONE_MINUTE >= self.switch:
            self.warn_work_end()

    def rest_tick(self):
        rest_len = ONE_MINUTE * self.rest_scl.get()
        now_ = now()
        if self.last_input_time > now_ - 0.5 * ONE_SECOND:
            # extend the rest interval to make the user rest longer
            LOG.info("you cheated but I caught you! %s > %s",
                     self.last_input_time.time(), self.switch.time())
            # make the user pay for their transgression!
            self.end += 10 * ONE_SECOND
        elif self.last_input_time + rest_len < now_:
            LOG.debug("thanks for resting, you can work again.")
            self.work()

    def set_work_bounds(self, dt: datetime.datetime) -> None:
        "define work bounds in datetime terms"
        self.start = dt
        self.switch = self.start + ONE_MINUTE * self.work_scl.get()
        self.end = self.switch + ONE_MINUTE * self.rest_scl.get()

    def set_rest_bounds(self, dt: datetime.datetime) -> None:
        "define rest bounds in datetime terms"
        self.start = dt - ONE_MINUTE * self.work_scl.get()
        self.switch = dt
        self.end = self.switch + ONE_MINUTE * self.rest_scl.get()

    def increment_bounds(self, delta: datetime.timedelta) -> None:
        "adjust work/rest bounds"
        self.start += delta
        self.switch += delta
        self.end += delta


def now():
    "shorthand"
    return datetime.datetime.now(tz=datetime.timezone.utc)


def epoch_seconds(dt):
    "hackish shorthand - hopefully just temporary though"
    return (dt - START).total_seconds()


async def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    levels = set(a for a in dir(logging) if re.match("^[A-Z]+$", a))
    levels.discard("NOTSET")
    parser.add_argument("-h", "--help", dest="help",
                        action="store_true", default=False)
    parser.add_argument("-l", "--loglevel", dest="level",
                        choices=levels, default="WARNING")
    parser.add_argument("-w", "--work", dest="work", type=float, default=10.0)
    parser.add_argument("-r", "--rest", dest="rest", type=float, default=3.0)
    parser.add_argument("-g", "--geometry", dest="geometry", default="")
    parser.add_argument("-c", "--control", dest="control",
                        choices=["fascist", "friendly"])
    (options, args) = parser.parse_known_args()

    if options.help:
        usage()
        return 0

    if args:
        usage(f"extra arguments on command line: {args!r}")
        return 1

    logging.basicConfig(
        level=options.level,
        style='{',
        format='{asctime} {levelname} {message}'
    )
    logging.Formatter.converter = time.gmtime

    app = AsyncTk()
    app.title("Typing Watcher")
    if options.geometry:
        app.geometry(options.geometry)
    task = Task(parent=app, work=options.work, rest=options.rest,
                control=options.control)
    task.pack()

    # Thanks to the python-list@python.org peeps for this bit of
    # window manager magic, esp Cameron Simpson.
    app.wait_visibility()
    subprocess.run(["/usr/bin/wmctrl", "-r", "'Typing Watcher'", # nosec
                    "-b", "add,sticky"])

    await app.run()
    return 0


def usage(msg="") -> None:
    if msg:
        print(msg, file=sys.stderr)
        print(file=sys.stderr)
    print(usage_text(), file=sys.stderr)
    sys.exit()


def usage_text() -> str:
    return __doc__.format(**globals())


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit()
