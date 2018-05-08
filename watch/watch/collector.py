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
        now = self.now()
        self.log.debug("idle: %s", (now - self.time))
        return self.time, self.work, self.rest, now

    def tick(self):
        self.time = self.now()
        self.log.debug("tick now: %s", self.time)
        return self.get()

    def put(self, work, rest):
        """Save the work/rest times (timedeltas).

        Note that the actual Tk scale widgets may well not support floats.
        """
        self.log.debug("work: %s, rest: %s", work, rest)
        self.work = work
        self.rest = rest
