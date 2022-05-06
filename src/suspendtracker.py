"""track computer's suspend and wake times"""

# This relies on the actions of
# /usr/lib/systemd/system-sleep/track-suspensions, replicated here in
# toto:

## #!/bin/sh

## echo "`date --iso-8601=seconds` $1 $2" >> /tmp/suspensions
## chmod 0644 /tmp/suspensions

import datetime
import logging
import os
import tempfile

import dateutil.parser

EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
SUSP_FILE = os.path.join(tempfile.gettempdir(), "suspensions")

LOG = logging.getLogger()

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
        "process suspensions file, picking up from the last point"
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
        "time the computer last woke up"
        return self.wake

    def last_sleep_length(self):
        "how long the computer was last asleep"
        return self.wake - self.suspend
