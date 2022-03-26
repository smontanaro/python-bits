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
-f             - toggle fascist setting (defaults to True)

Watch is a Tk-based program that monitors work and rest times for keyboard
and mouse use to help users avoid overuse that can lead to or exacerbate
repetitive strain injuries.  The user can define the duration of work and
rest intervals.  In fascist mode, the user can't override the displayed rest
window.  In friendly mode, a cancel button is available to allow the user to
prematurely terminate the rest interval. The user interface includes a rest
button to allow the user to immediately end the current work interval.

Activity of the mouse and possibly the keyboard is tracked.  Mouse position
can be determined via Tk, but monitoring keyboard activity is not currently
possible in a platform-independent way. During the work interval, if no
activity is sensed for at least the duration of the rest interval, the work
interval is reset and the user can continue working.  It is not always
possible to track keystrokes, but in these days of graphical user
interfaces, it is unlikely the mouse will stay put for long if the user is
actively using the computer.

If no direct detection of keyboard activity is possible on your platform but
you have Emacs available, you can add an auto-save-hook that jiggles the
pointer by a few pixels so the typing watcher will notice the activity.  It
toggles the jiggle direction so that the next time it jiggles the mouse the
other way.  The following code uses set-mouse-pixel-position and
mouse-pixel-position which are both available in recent versions of GNU
Emacs and XEmacs::

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

"""

import getopt
import logging
import os
import sys
import time
from tkinter import (Canvas, Frame, StringVar, Label, Scale, Radiobutton,
                     Button, Tk, Toplevel, LEFT, HORIZONTAL, simpledialog)
# # Eventually?
# from tkinter import (Canvas, StringVar, Tk, Toplevel, LEFT, HORIZONTAL,
#                      simpledialog)
# from tkinter.ttk import (Frame, Label, Scale, Button, Frame, Radiobutton)

LID_STATE = "/proc/acpi/button/lid/LID0/state"
WORK_TM = 10
REST_TM = 3
PROG = os.path.split(sys.argv[0])[-1]

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

    def __init__(self, master=None, **kw):
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

        self.rect = None
        Canvas.__init__(*(self, master), **kw)

    def set_range(self, mn, mx):
        self.min = mn
        self.max = mx

    def set(self, value):
        if self.rect is not None:
            self.delete(self.rect)
        metheight = int(self.cget("height")) + 1
        canwidth = int(self.cget("width"))
        metwidth = canwidth * (value - self.min) / (self.max - self.min)
        self.rect = self.create_rectangle(
            0, 0, metwidth, metheight, outline="red", fill="red")
        self.update()

    def reset(self):
        self.set(self.min)


class Task(Frame):  # pylint: disable=too-many-ancestors
    WORKING = 1
    RESTING = 0
    # needs to be 1000 so display update intervals are consistent when
    # resting
    CHK_INT = 95  # milliseconds

    # keyed by sys.platform or "default" to return a method that checks
    # for mouse/keyboard activity
    activity_dispatch = {}

    def __init__(self, master=None, work=WORK_TM, rest=REST_TM, fascist=True, debug=0):
        """create the task widget and get things started"""

        # various inits
        self.log = logging.getLogger(__name__)
        self.mouse_pos = None
        self.old_work = 0.0
        self.then = 0
        self.state = self.WORKING
        self.cancel_rest = 0
        self.resttext = ""
        self.mouse_counts = 0
        self.lid_state = "open"
        self.lid_time = time.time()
        self.interrupt_count = 0

        Frame.__init__(*(self, master))

        self.style = StringVar()
        self.style.set("fascist" if fascist else "friendly")

        # create main interactor window
        self.workmeter = Meter(self, background="grey50")
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
        dictator = Radiobutton(
            f3, text="Fascist", variable=self.style, value="fascist")
        friend = Radiobutton(
            f3, text="Friendly", variable=self.style, value="friendly")
        dictator.pack(side=LEFT)
        friend.pack(side=LEFT)

        f4 = Frame(self)
        f4.pack()
        restb = Button(f4, text="Rest", command=self.rest)
        restb.pack(side=LEFT)
        stop = Button(f4, text="Quit", command=self.quit)
        stop.pack(side=LEFT)
        help_ = Button(f4, text="Help", command=self.help_)
        help_.pack(side=LEFT)

        # create the cover window
        self.cover = Toplevel(background="black")
        self.cover.withdraw()
        # user can't resize it
        self.cover.resizable(0, 0)
        (w, h) = (self.winfo_screenwidth(), self.winfo_screenheight())
        if debug:
            # just a small window when debugging
            (w, h) = (w // 8, h // 8)
        self.cover.geometry(f"{w}x{h}+0+0")

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

        # initialize interrupt information
        self.interrupt_time = time.time()
        self.interrupts = self.get_interrupts()

        self.bgcolor = self["background"]

        # start the ball rolling
        self.work()
        self.check_interval = self.CHK_INT
        self.after(self.check_interval, self.tick)

    def reset_duration(self, _dummy):
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

    def which_state(self):
        if self.state == self.WORKING:
            return "working"
        return "resting"

    def work(self):
        """start the work period"""
        self.reset_warning()
        self.restmeter.reset()
        self.state = self.WORKING
        now = time.time()
        self.then = now + self.work_scl.get() * 60
        self.workmeter.set_range(now, self.then)
        self.workmeter.set(now)
        self.cover.withdraw()

        self.log.debug("work: state: %s now: %s then: %s",
                       self.which_state(), hhmm(now), hhmm(self.then))

    def warn_work_end(self):
        """alert user that work period is almost up"""
        self.set_background("yellow")

    def reset_warning(self):
        """back to plain old grey bg"""
        self.set_background(self.bgcolor)

    def set_background(self, color):
        already = set()
        def set_bg(w, indent=0):
            for child in w.winfo_children():
                child["background"] = color
                if child not in already:
                    already.add(child)
                    set_bg(child, indent+1)
        self["background"] = color
        set_bg(self)

    def rest(self):
        """overlay the screen with a window, preventing typing"""
        self.cancel_rest = 0
        self.workmeter.reset()
        self.state = self.RESTING
        now = time.time()
        self.then = now + self.rest_scl.get() * 60
        self.cover.deiconify()
        self.cover.tkraise()
        self.resttext = (f"Rest for {self.rest_scl.get()}m00s please...")
        self.restnote.configure(text=self.resttext)
        self.restmeter.set_range(now, self.then)
        self.restmeter.set(now)
        if self.style.get() == "friendly":
            self.cancel_button.pack(pady=2)
        else:
            self.cancel_button.pack_forget()

        self.log.debug("rest: state: %s now: %s then: %s",
                       self.which_state(), hhmm(now), hhmm(self.then))

    def help_(self):
        d = simpledialog.SimpleDialog(
            self.master,
            text=usageText(),
            buttons=["Done"],
            default=0,
            title="Help")
        d.go()

    def get_interrupts(self):
        """get mouse/keyboard activity info

        where possible, call platform-dependent routine to get mouse and
        keyboard info, otherwise, just return mouse info

        in all cases, the value returned should be a value that increases
        monotonically with activity
        """
        count = (self.activity_dispatch.get(sys.platform)
                 or self.activity_dispatch["default"])(self)
        self.log.debug("interrupts: %s", count)
        return count

    def get_mouseinfo(self):
        if self.lid_state == "closed":
            return self.mouse_counts
        ptr_xy = self.winfo_pointerxy()
        if self.mouse_pos is None:
            self.mouse_pos = ptr_xy
        mouse_pos = ptr_xy
        if mouse_pos != self.mouse_pos:
            self.mouse_pos = mouse_pos
            self.mouse_counts += 1
        return self.mouse_counts

    activity_dispatch["default"] = get_mouseinfo

    def get_linux_interrupts(self):
        if self.lid_state == "closed":
            return self.interrupt_count
        count = 0
        # Can't seem to find mouse interrupts, so for now, just watch
        # keyboard and mix add get_mouseinfo() output as a substitute for
        # mouse interrupts.
        with open("/proc/interrupts", encoding="utf-8") as interrupts:
            for line in interrupts:
                fields = line.split()
                if fields[0] == "1:":
                    count = sum(int(fields[n]) for n in range(1, 8))
                    self.interrupt_count = count
                    break
        return self.interrupt_count + self.get_mouseinfo()

    activity_dispatch["linux"] = get_linux_interrupts

    def check_lid_state(self):
        if os.path.exists(LID_STATE):
            with open(LID_STATE, encoding="utf-8") as lid:
                for line in lid:
                    fields = line.strip().split()
                    if fields[0] == "state:":
                        state = fields[1]
                        if state != self.lid_state:
                            self.log.debug("lid state changed: %s", state)
                            self.lid_state = state
                            self.lid_time = time.time()

    def tick(self):
        """perform periodic checks for activity or state switch"""
        # check for mouse or keyboard activity
        now = time.time()
        self.check_lid_state()
        interrupts = self.get_interrupts()
        if interrupts > self.interrupts:
            self.interrupt_time = now
            self.interrupts = interrupts

            self.log.debug("tick (1): state: %s now: %s then: %s",
                           self.which_state(), hhmm(now), hhmm(self.then))

        if self.state == self.RESTING:
            # if there is an input interrupt since the start of the rest
            # interval extend the interval by 10 seconds
            if self.interrupt_time > self.restmeter.min:
                self.then = self.then + 10
                self.restmeter.set_range(self.restmeter.min, self.then)
                self.restmeter.set(now)
                self.interrupt_time = self.restmeter.min

                self.log.debug("tick (2): state: %s start: %s now: %s then: %s",
                               self.which_state(), hhmm(self.restmeter.min),
                               hhmm(now), hhmm(self.then))

            if self.cancel_rest or now > self.then:
                self.state = self.WORKING
                self.work()
            else:
                self.cover.tkraise()

                # update message to reflect rest time remaining
                timeleft = int(self.then - now)
                minleft = timeleft // 60
                secleft = timeleft % 60
                self.resttext = (f"Rest for {minleft}m{secleft:02d}s please...")
                self.log.debug(self.resttext)
                self.restnote.configure(text=self.resttext)

                self.log.debug("tick (4): state: %s", self.which_state())

        else:
            # if it's been at least the length of the rest interval
            # since new interrupt, reset the work interval
            if self.interrupt_time + self.rest_scl.get() * 60 < now:
                self.work()

            if self.interrupt_time < now:
                # work interval can extend for long periods of time during
                # idle periods, so back off on the check interval to a
                # maximum of once every five seconds as long as there is no
                # activity
                self.check_interval = int(min(self.check_interval * 1.3, 5000))
            else:
                self.check_interval = self.CHK_INT

            if now > self.then:
                # work period expired
                self.state = self.RESTING
                # reset the check interval since we may have extended it
                # during the just ending work interval
                self.check_interval = self.CHK_INT
                self.rest()
            elif now + 60 > self.then:
                # work period nearly expired - warn user
                self.warn_work_end()

        self.restmeter.set(now)
        self.workmeter.set(now)
        self.after(self.check_interval, self.tick)

    def cancel(self):
        self.cancel_rest = 1

def hhmm(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


FORMAT = '{asctime} {levelname} {message}'
def main(args):
    work, rest, geometry, fascist, debug = parse(args)
    logging.basicConfig(
        level="DEBUG" if debug else "INFO",
        style='{',
        format=FORMAT
    )
    app = Tk()
    app.title("Typing Watcher")
    if geometry:
        app.geometry(geometry)
    task = Task(master=app, work=work, rest=rest, fascist=fascist, debug=debug)
    task.pack()
    app.mainloop()


def usage(name):
    print("Usage", name, file=sys.stderr)
    print(usageText(), file=sys.stderr)
    sys.exit()


def usageText():
    return __doc__.format(**globals())

def parse(args):
    opts = getopt.getopt(args[1:], "dhw:r:g:f",
                         ['debug', 'help', 'work=', 'rest=', 'geometry=',
                          'friendly', 'fascist'])
    options = opts[0]

    # defaults
    work = 10.0
    rest = 3.0
    geometry = ""
    debug = 0
    fascist = True

    for opt, val in options:
        if opt in ['-h', '--help']:
            usage(args[0])
        elif opt in ['-d', '--debug']:
            debug = 1
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

    return work, rest, geometry, fascist, debug


if __name__ == "__main__":
    main(sys.argv)
    sys.exit()
