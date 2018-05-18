from __future__ import print_function

import time
import logging

EPOCH = 0

class Collector:
    def __init__(self):
        self.time = EPOCH
        self.log = logging.getLogger(__name__)
        self.work = 20
        self.rest = 3

    def now(self):              # pylint: disable=no-self-use
        return time.time()

    def get(self):
        "Return latest tick time, work length, rest length, and current time."
        now = self.now()
        self.log.debug("idle: %s", (now - self.time))
        return self.time, self.work, self.rest, now

    def tick(self):
        "Update latest tick time."
        self.time = self.now()
        self.log.debug("tick now: %s", self.time)

    def put(self, work, rest):
        "Update the work & rest times."
        self.log.debug("work: %s, rest: %s", work, rest)
        self.work = work
        self.rest = rest
