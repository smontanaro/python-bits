#!/usr/bin/env python3

# watch.py - keep an eye on the display and tell the user when to
# rest
# Author: Skip Montanaro (skip@mojam.com)
# $Id: watch.py,v 1.5 2000/06/18 03:42:24 skip Exp $

# Updated for Python 3 2018/04/26
"""Usage: {PROG} [ -w min ] [ -r min ] [-g geometry ] [ -h ] [ -f | --fascist | --friendly ]

--work=minutes - set work time in minutes (default: {WORK_TM})
--rest=minutes - set rest time in minutes (default: {REST_TM})
--geometry=geo - geometry in typical X fashion
--fascist      - set initial style to 'fascist'
--friendly     - set initial style to 'friendly'
-f             - toggle fascist setting between fascist and friendly
--debug        - debug logging

Watch is a Tk-based program that monitors work and rest times for keyboard
and mouse use to help users avoid overuse that can lead to or exacerbate
repetitive strain injuries.  The user can define the duration of work and
rest intervals.  In fascist mode, the user can't override the displayed rest
window.  In friendly mode, a cancel button is available to allow the user to
prematurely terminate the rest interval. The user interface includes a rest
button to allow the user to immediately end the current work interval.

Activity of the mouse and keyboard is tracked using pynput. I have no
idea how platform-independent that is. At the moment, my only platform
is XUbuntu running Xorg.

"""

import asyncio
import datetime
import enum
import getopt
import logging
import os
import sys
import time
from tkinter import (Canvas, Frame, StringVar, Label, Scale, Radiobutton,
                     Button, Tk, Toplevel, LEFT, HORIZONTAL, simpledialog)
from typing import Tuple

import dateutil.parser
import pynput

SUSP_FILE = "/tmp/suspensions"
EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
WORK_TM = 10
REST_TM = 3
PROG = os.path.split(sys.argv[0])[-1]

NORMAL_COLOR = "grey75"
ALERT_COLOR = "yellow"

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

    def set_range(self, mn : int, mx : int) -> None:
        self.min = mn
        self.max = mx

    def set(self, value : int) -> None:
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

CHK_INT = 500                   # milliseconds

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
            await asyncio.sleep(0.05) # obviously, sleep time could be parameterized

    def stop(self):
        self.running = False

    async def run(self):
        await asyncio.gather(*self.runners)


class WakeSuspend:
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
        LOG.debug("last sleep time: %s", self.wake - self.suspend)


class Task(Frame):  # pylint: disable=too-many-ancestors
    "The base for the entire application"

    def __init__(self, parent=None, work=WORK_TM, rest=REST_TM, fascist=True,
                 debug=False) -> None:
        """create the task widget and get things started"""

        # various inits
        self.parent = parent
        self.old_work = 0.0
        self.then = 0
        self.state = wstate.WORKING
        self.cancel_rest = False
        self.warned = False
        self.wake_suspend = WakeSuspend()
        Frame.__init__(*(self, parent))

        self.style = StringVar()
        self.style.set("fascist" if fascist else "friendly")

        # create main interactor window
        self.workmeter = Meter(self, background=NORMAL_COLOR)
        self.workmeter.pack()

        f1 = Frame(self)
        f1.pack()
        Label(f1, text="Work time:").pack(side=LEFT)
        self.work_scl = Scale(
            f1,
            orient=HORIZONTAL,
            from_=1,
            to=max(45, work),
            command=self.reset_duration)
        self.work_scl.set(work)
        self.work_scl.pack(side=LEFT)

        f2 = Frame(self)
        f2.pack()
        Label(f2, text="Rest time:").pack(side=LEFT)
        self.rest_scl = Scale(
            f2,
            orient=HORIZONTAL,
            from_=1,
            to=max(15, rest),
            command=self.reset_duration)
        self.rest_scl.set(rest)
        self.rest_scl.pack(side=LEFT)

        f3 = Frame(self)
        f3.pack()
        Radiobutton(f3, text="Fascist", variable=self.style,
                    value="fascist").pack(side=LEFT)
        Radiobutton(f3, text="Friendly", variable=self.style,
                    value="friendly").pack(side=LEFT)

        f4 = Frame(self)
        f4.pack()
        Button(f4, text="Rest", command=self.rest).pack(side=LEFT)
        Button(f4, text="Quit", command=parent.stop).pack(side=LEFT)
        Button(f4, text="Help", command=self.help_).pack(side=LEFT)

        kb_listen = pynput.keyboard.Listener(on_press=self.handle_input,
                                             on_release=self.handle_input)
        kb_listen.daemon = True
        kb_listen.start()
        mouse_listen = pynput.mouse.Listener(on_click=self.handle_input,
                                             on_scroll=self.handle_input,
                                             on_move=self.handle_input)
        mouse_listen.daemon = True
        mouse_listen.start()

        # create the cover window
        self.cover = Toplevel(background="black")
        self.cover.withdraw()
        # user can't resize it
        self.cover.resizable(False, False)
        (w, h) = (self.winfo_screenwidth(), self.winfo_screenheight())
        if debug:
            # just a small window when debugging
            (w, h) = (w // 8, h // 8)
        self.cover.geometry(f"{w}x{h}+0+0")

        # and it's undecorated
        self.cover.overrideredirect(True)

        # cover contains a frame with rest message and meter
        f = Frame(self.cover, background="black")
        self.restnote = Label(f, background="black", foreground="white")
        self.restmeter = Meter(f, background=NORMAL_COLOR, height=10, width=200)
        self.restnote.pack(pady=2)
        self.restmeter.pack(fill="x", expand=1, pady=2)
        self.cancel_button = Button(f, text="Cancel Rest", command=self.cancel)
        f.pack()

        # initialize interrupt information
        self.last_input_time = int(time.time())

        self.set_background(NORMAL_COLOR)

        # start the ball rolling
        self.work()
        self.check_interval = CHK_INT
        self.after(self.check_interval, self.tick)

    def reset_duration(self, _dummy=None) -> None:
        """reset work/rest interval lengths to current scale values"""
        wtime = self.work_scl.get()
        self.workmeter.set_range(self.workmeter.min,
                                 self.workmeter.min + wtime * 60)
        self.restmeter.set_range(self.restmeter.min,
                                 self.restmeter.min + self.rest_scl.get() * 60)
        # only time the user can fiddle the work/rest meters is during
        # the work phase, so the only scale change that matters for extending
        # or contracting the end of the interval is the work scale
        if self.old_work:
            delta = wtime - self.old_work
        else:
            delta = 0
        self.then += delta * 60
        self.old_work = wtime

    def work(self) -> None:
        """start the work period"""
        self.reset_warning()
        self.restmeter.reset()
        self.state = wstate.WORKING
        now = int(time.time())
        self.then = now + self.work_scl.get() * 60
        self.workmeter.set_range(now, self.then)
        self.workmeter.set(now)
        self.cover.withdraw()
        self.check_interval = CHK_INT
        self.cancel_rest = False

        LOG.debug("work: state: %s now: %s then: %s",
                  self.state.value, hhmm(now), hhmm(self.then))

    def warn_work_end(self) -> None:
        """alert user that work period is almost up"""
        if self.warned:
            return
        # work period nearly expired - warn user
        LOG.debug("Careful pardner, time's almost up.")
        self.warned = True
        self.set_background(ALERT_COLOR)

    def reset_warning(self) -> None:
        """back to plain old grey bg"""
        self.set_background(NORMAL_COLOR)

    def extend_check_interval(self):
        "maybe lengthen check interval"
        # work interval can extend for long periods of time during
        # idle periods, so back off on the check interval to a
        # maximum of once every five seconds as long as there is no
        # activity
        self.check_interval = int(min(self.check_interval * 1.3, 5000))

    def set_background(self, color) -> None:
        def set_bg(w, indent=0):
            for child in w.winfo_children():
                child["background"] = color
                set_bg(child, indent+1)
        self["background"] = color
        set_bg(self)

    def rest(self) -> None:
        """overlay the screen with a window, preventing typing"""
        self.cancel_rest = False
        self.workmeter.reset()
        self.state = wstate.RESTING
        now = int(time.time())
        self.then = now + self.rest_scl.get() * 60
        self.cover.deiconify()
        self.cover.tkraise()
        self.restnote.configure(text=f"Rest for {self.rest_scl.get()}m00s please...")
        self.restmeter.set_range(now, self.then)
        self.restmeter.set(now)
        if self.style.get() == "friendly":
            self.cancel_button.pack(pady=2)
        else:
            self.cancel_button.pack_forget()
        self.check_interval = CHK_INT

        LOG.debug("rest: state: %s now: %s then: %s",
                  self.state.value, hhmm(now), hhmm(self.then))

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
        # check for mouse or keyboard activity
        now = int(time.time())
        LOG.debug("tick, last input @ %s",
                  datetime.datetime.fromtimestamp(self.last_input_time))
        self.wake_suspend.check_suspensions()

        if self.state == wstate.WORKING:
            if now - self.last_input_time >= 60:
                self.then += 60
                LOG.debug("add a minute to work interval (%d)", self.then)
                # fudge an input
                self.last_input_time = now - 1
                self.workmeter.set_range(now, self.then)
                self.workmeter.set(now)
                self.reset_warning()
            elif now >= self.then:
                LOG.debug("time's up!")
                self.rest()
            elif now + 60 > self.then:
                self.warn_work_end()
            else:
                self.extend_check_interval()

        elif self.state == wstate.RESTING:
            if self.last_input_time >= self.restmeter.min:
                LOG.debug("you tried to cheat but I caught you!")
                # extend rest interval
                self.then += 10
                self.restmeter.set_range(self.restmeter.min, self.then)
                self.restmeter.set(now)
                self.last_input_time = self.restmeter.min
                self.cover.tkraise()
                self.check_interval = CHK_INT
            elif self.last_input_time + self.rest_scl.get() * 60 < now:
                LOG.debug("thanks for resting, you can work again.")
                self.work()
            else:
                self.cover.tkraise()
                # update message to reflect rest time remaining
                timeleft = self.then - now
                minleft = timeleft // 60
                secleft = timeleft % 60
                self.restnote.configure(text=f"Rest for {minleft}m{secleft:02d}s please...")
                self.extend_check_interval()

        else:
            LOG.error("unknown state: %r", self.state)
            raise ValueError(f"unknown state {self.state!r}")

        self.restmeter.set(now)
        self.workmeter.set(now)
        self.after(self.check_interval, self.tick)

    def cancel(self) -> None:
        self.cancel_rest = True

    def handle_input(self, *_args):
        "handle all keyboard & mouse activity"
        # don't care about the actual events, just update interrupt time
        self.last_input_time = int(time.time())
        self.check_interval = CHK_INT

def hhmm(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


FORMAT = '{asctime} {levelname} {message}'
async def main(args) -> int:
    work, rest, geometry, fascist, debug = parse(args)
    logging.basicConfig(
        level="DEBUG" if debug else "INFO",
        style='{',
        format=FORMAT
    )
    app = AsyncTk()
    app.title("Typing Watcher")
    if geometry:
        app.geometry(geometry)
    task = Task(parent=app, work=work, rest=rest, fascist=fascist, debug=debug)
    task.pack()

    # Thanks to the python-list@python.org peeps for this bit of
    # window manager magic, esp Cameron Simpson.
    app.wait_visibility()
    os.system("wmctrl -r 'Typing Watcher' -b add,sticky")

    await app.run()
    return 0

def usage(name : str) -> None:
    print("Usage", name, file=sys.stderr)
    print(usage_text(), file=sys.stderr)
    sys.exit()


def usage_text() -> str:
    return __doc__.format(**globals())

def parse(args) -> Tuple[float, float, str, bool, bool]:
    opts = getopt.getopt(args[1:], "dhw:r:g:f",
                         ['debug', 'help', 'work=', 'rest=', 'geometry=',
                          'friendly', 'fascist'])
    options = opts[0]

    # defaults
    work = 10.0
    rest = 3.0
    geometry = ""
    debug = False
    fascist = True

    for opt, val in options:
        if opt in ['-h', '--help']:
            usage(args[0])
        elif opt in ['-d', '--debug']:
            debug = True
        elif opt in ['-w', '--work']:
            work = float(val)
        elif opt in ['-r', '--rest']:
            rest = float(val)
        elif opt in ['-g', '--geometry']:
            geometry = val
        elif opt == '-f':
            fascist = not fascist
        elif opt == '--friendly':
            fascist = False
        elif opt == '--fascist':
            fascist = True

    if rest > work:
        usage(args[0])

    return (work, rest, geometry, fascist, debug)


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
    sys.exit()
