#!/usr/bin/env python

# Some musings about date and time recurrence relations.
# 
# Conceptually, a recurring time specification can be thought of as an
# equation of sorts.  When you plug a specific time into it, you can 'solve'
# the equation to answer whether or not that specific time is contained in or
# overlaps with the times specified by the recurrence.  Alternatively, you can
# perform intersection or union operations between recurrences and specific
# dates to form new recurrences or perform an inclusion test.  All you have to
# do is develop a consistent algebra that defines the elementary operations
# you support.
# 
# If we want to represent a polynomial, say
# 
#     x**3 - 2*x**2 + 4
# 
# it's sufficient to store the coefficients for the various powers of x:
# 
#     (1, -2, 0, 4)
# 
# A straightforward translation into dates and times might yield the following
# 'powers':
# 
#     year
#     month
#     day
#     time
#     weekday
# 
# Note that they aren't mutually exclusive like the powers of x in the
# polynomial above, so we shouldn't expect to use normal arithmetic operations
# to 'solve' such equations.
# 
# How might we represent 'the first of every month'?  The following seems
# reasonable:
# 
#     year	*
#     month	*
#     day	1
#     time	*
#     weekday	*
# 
# where '*' means 'any' or 'don't care'.
# 
# How might 'every Monday, Wednesday and Friday from 1-3pm' be represented?
# 
#     year	*
#     month	*
#     day	*
#     time	1300-1500
#     weekday	M/W/F
# 
# Given this representation of a date formula, we'd like to perform a few
# basic operations:
# 
#     1. Check to see if a specific date is covered by the recurrence.
# 
#     2. Generate a finite subset of dates/times from the recurrence.
# 
#     3. Perform intersections or unions with other recurrences to represent
#        more complex recurrences.
# 
# A specific date can be represented as a degenerate recurrence.  Consider
# 2:30pm, September 24, 1990.  Its representation is
# 
#     year	1990
#     month	9
#     day	24
#     time	1430
#     weekday	M
# 
# Intersecting that with our MWF 1-3pm recurrence we get
# 
#     year	1990
#     month	9
#     day	24
#     time	1430
#     weekday	M
# 
# This gives us a valid (nonempty) recurrence as a result, so we know that
# 9/24/90 @ 2:30pm is a date covered by the recurrence.
# 
# Given a starting date, a timespan and a step size, we can generate a finite
# subset of the infinite series represented by a recurrence by stepping
# through the timespan, incrementing by the step size each time.  Again,
# working with our MWF 1-3pm recurrence example, we can generate a series of
# specific dates between September 23, 1990 and October 3, 1990 stepping one
# day at a time repeatedly using the same intersection operation we used:
# 
#     for date from 9/23/90 to 10/3/90, in one-day increments:
# 	generate a new finite recurrence for date
# 	intersect the new recurrence with MWF 1-3pm
# 	if the intersection is not empty:
# 	    emit the intersection
# 
# Performing intersections and unions between two recurrences might get a
# little tricky.  Let's try something simple. Intersect MWF 1-3pm with TTh
# 2-4pm:
# 
#     year	*
#     month	*
#     day	*
#     time	1400-1500
#     weekday	None
# 
# The presence of None in the weekday field indicates that the intersection of
# the weekdays from the two recurrences was empty.  A None in any field
# indicates an invalid recurrence.
# 
# Now, try a union of the two example recurrences:
# 
#     year	*
#     month	*
#     day	*
#     time	1300-1600
#     weekday	M/T/W/Th/F
# 
# Intersecting the TTh 2-4pm recurrence with 'the first of every month' yields:
# 
#     year	*
#     month	*
#     day	1
#     time	1400-1600
#     weekday	T/Th
# 
# that is, 'the first of every month that is a Tuesday or Thursday between 2pm
# and 4pm'.
# 
# This simple structure does not allow you to represent some other types of
# recurrences that occur frequently.  For instance, it can't represent 'the
# third Thursday of the month', Easter or 'leap years between 1900 and 2000'.
# Deciding if that extra capability is needed and how to represent it is not
# obvious.  One possibility is to make the fields more complex.  The former
# recurrence might be represented as
# 
#     year	*
#     month	*
#     day	*
#     time	*
#     weekday	Th:3
# 
# (though that's a bit unpleasing - does ':3' mean the third Thursday of the
# month or the third Thursday of the year?)  while its not at all obvious how
# to represent the latter.  Even though we can think of a potential
# representation for 'the third Thursday of every month', we did it by
# complicating the representation of individual 'coefficients' in our
# equation.  (The military representation of clock time is not strictly
# numeric either, but we'll gloss over that for now.)
# 
# Let's assume that the 'w:n' notation indicates the nth occurence of weekday
# w in the specified month and that '*' implies 'any'.  'Every Monday' is
# generally representable as
# 
#     ...
#     weekday	M:*
# 
# or more succintly:
# 
#     ...
#     weekday	M
# 
# What do the individual operations look like?  For year, month, day and time
# fields, we can have individual numbers or more generally, tuples
# representing a range.  We can extend that slightly without overcomplicating
# things much to allow representation of multiple ranges within one field.
# For instance, the years 1968, 1992 and 2005 can be represented as
# 
#     year (1968, 1992, 2005)
# 
# The range of years 1968 to 1972 and the year 1999 can be represented as
# 
#     year ((1968, 1972), 1999)
# 
# Internally, it seems best to always represent individual values as
# degenerate ranges to make calculations more uniform:
# 
#     year ((1968, 1972), (1999, 1999))
# 
# though for ease of reading by non-programmers it's best to avoid
# exposing the tuple representation altogether:
# 
#     year 1968-1972 or 1999
# 
# Intersection and union of year, month, day and time fields is
# straightforward.  Just perform the relevant operation piecewise and reduce
# to 'lowest common denominator'.  Intersecting ((1968, 1972), (1999, 1999))
# with ((1970, 1975)) yields ((1970, 1972),) The union is ((1968, 1972),
# (1970, 1975), (1999, 1999)) or ((1968, 1975), (1999, 1999)) after merging
# ranges that overlap.
# 
# Intersecting '*' with a specific value always yields the specific value.
# Unioning '*' with a specific value always yields '*'.  Intersection or union
# of fields whose value is None always yields None.
# 
# Performing intersections and unions with weekday fields is straight set
# intersection/union with the same conventions about '*' and None as given
# above.  (Internally I represent weekdays and numbers, where Monday == 0.)
# 
# Unsolved problem: How do you represent the union of TTh 2-4pm with 'the
# first of every month'?  At first glance, it might seem that you'd get
# 
#     year	*
#     month	*
#     day	*
#     time	*
#     weekday	*
# 
# but that obviously isn't right.  You want 'the first of every month *or*
# TTh 2-4pm'.  It may be necessary to maintain a tree structure whose leaves
# are recurrences and whose interior nodes are operators (e.g., &&, ||, ~).

__version = "0.2"

import time, string, DateTime

class Recurrence:
    def __init__(self, dt=None):
	"""represent a recurring date or time

	Each field is either * (means 'any' or 'don't care'), None
	(means invalid), or tuple of int pairs (means one or more
	ranges)
	"""

	self.year = self.month = self.day = self.time = self.weekday = "*"
	if dt is not None:
	    self.set_timetuple(dt.tuple())

    def set_timetuple(self, timetuple):
	"""set year, month, day, time, weekday from a time tuple

	The time tuple must be at least three elements long (y, m, d).  If
	present, the hour and minute are used to build a time.  The second
	and weekday fields are ignored.  The weekday is computed by building
	a new time tuple and asking the time module to compute it.
	"""

	if len(timetuple) < 3:
	    raise ValueError, "need at least year, month and day values"

	self.set_year(timetuple[0])
	self.set_month(timetuple[1])
	self.set_day(timetuple[2])
	if len(timetuple) >= 5:
	    self.set_hhmm(timetuple[3], timetuple[4])

	if len(timetuple) >= 6:
	    wkday = time.localtime(time.mktime(timetuple[0:3]+(0,)*6))[6]
	    self.set_weekday(wkday)

    def set_weekdays(self, days):
	"""set weekday to the input value - must be tuple or list of weekdays"""
	days = list(days)
	days.sort()
	self.set_weekday(days[0])
	for d in days[1:]: self.add_weekday(d)

    def set_year(self, year): self.year = ((year, year),)
    def set_month(self, month): self.month = ((month, month),)
    def set_day(self, day): self.day = ((day, day),)
    def set_hhmm(self, hh, mm): t = hh*60+mm ; self.time = ((t, t),)
    def set_weekday(self, wkday): self.weekday = ((wkday,wkday),)

    def add_year(self, year):
	if self.year == "*": self.year = ((year, year),)
	else: self.year = self.year + ((year, year),)

    def add_month(self, month):
	if self.month == "*": self.month = ((month, month),)
	else: self.month = self.month + ((month, month),)

    def add_day(self, day):
	if self.day == "*": self.day = ((day, day),)
	else: self.day = self.day + ((day, day),)

    def add_hhmm(self, hh, mm):
	t = hh*60+mm
	if self.time == "*": self.time = ((t, t),)
	else: self.time = self.time + ((t, t),)

    def add_weekday(self, wkday):
	if self.weekday == "*": self.weekday = ((wkday, wkday),)
	else: self.weekday = self.weekday + ((wkday, wkday),)

    def set_year_range(self, y1, y2): self.year = ((y1, y2),)
    def set_month_range(self, m1, m2): self.month = ((m1, m2),)
    def set_day_range(self, d1, d2): self.day = ((d1, d2),)
    def set_hhmm_range(self, h1, m1, h2, m2):
	t1 = h1*60+m1
	t2 = h2*60+m2
	if t1 > t2: t1, t2 = t2, t1
	self.time = ((t1, t2),)

    def add_year_range(self, y1, y2):
	if y1 > y2: y1, y2 = y2, y1
	if self.year == "*": self.year = ((y1, y2),)
	else: self.year = self.year + ((y1, y2),)

    def add_month_range(self, m1, m2):
	if m1 > m2: m1, m2 = m2, m1
	if self.month == "*": self.month = ((m1, m2),)
	else: self.month = self.month + ((m1, m2),)

    def add_day_range(self, d1, d2):
	if d1 > d2: d1, d2 = d2, d1
	if self.day == "*": self.day = ((d1, d2),)
	else: self.day = self.day + ((d1, d2),)

    def add_hhmm_range(self, h1, m1, h2, m2):
	t1 = h1*60+m1
	t2 = h2*60+m2
	if t1 > t2: t1, t2 = t2, t1
	if self.time == "*": self.time = ((t1, t2),)
	else: self.time = self.time + ((t1, t2),)

    def intersect(self, other):
	"""return intersection of two Recurrence objects"""
	i = Recurrence()
	i.year = self.intersect_field(self.year, other.year)
	i.month = self.intersect_field(self.month, other.month)
	i.day = self.intersect_field(self.day, other.day)
	i.time = self.intersect_field(self.time, other.time)
	i.weekday = self.intersect_field(self.weekday, other.weekday)
	return i

    def intersect_field(self, f1, f2):
	if f1 is None or f2 is None: return None
	if f1 == "*": return f2
	if f2 == "*": return f1
	intersection = []
	for t1 in f1:
	    for t2 in f2:
		t = (max(t1[0], t2[0]), min(t1[1], t2[1]))
		if t[0] <= t[1]: intersection.append(t)
	if not intersection: return None
	return tuple(intersection)

    def enumerate(self, start, end, step):
	"""return a list of recurrences between start and end

	start and end are DateTime objects - step is a DateTimeDelta object
	"""
	result = []
	while start <= end:
	    r = Recurrence(start)
	    i = self.intersect(r)
	    if not i.isnull():
		result.append(i.DateTime())
	    start = start + step
	return result

    def filter(self, list):
	"""filter a list of DateTime objects through the recurrence"""
	result = []
	for dt in list:
	    r = Recurrence(dt)
	    i = self.intersect(r)
	    if not i.isnull():
		result.append(dt)
	return result

    def isnull(self):
	return (self.year is None or self.month is None or self.day is None or
		self.time is None or self.weekday is None)

    def isrange(self):
	if (self.year == "*" or self.month == "*" or self.day == "*" or
	    self.time == "*" or self.weekday == "*"): return 1
	if len(self.year) > 1 or self.year[0][0] != self.year[0][1]:
	    return 1
	if len(self.month) > 1 or self.month[0][0] != self.month[0][1]:
	    return 1
	if len(self.day) > 1 or self.day[0][0] != self.day[0][1]:
	    return 1
	if len(self.time) > 1 or self.time[0][0] != self.time[0][1]:
	    return 1
	if len(self.weekday) > 1 or self.weekday[0][0] != self.weekday[0][1]:
	    return 1
	return 0

    # pretty printing methods - no algorithmic substance follows...
    def DateTime(self):
	"""return a DateTime object representing self"""
	if self.isnull(): raise ValueError, "null recurrence"
	if self.isrange(): raise ValueError, "not a concrete date and time"
	t = self.time[0][0]
	h = t / 60
	m = t % 60
	d = DateTime.DateTime(self.year[0][0], self.month[0][0],
			      self.day[0][0], h, m)
	return d

    def frepr(self, val, name):
	"""return printable representation of general field"""
	if val is None: return "%s=None" % name
	if val == "*": return "%s=*" % name
	ranges = []
	for v in val:
	    if v[0] == v[1]: ranges.append(`v[0]`)
	    else: ranges.append("%s-%s" % v)
	return "%s=%s" % (name, string.join(ranges, "/"))

    def trepr(self, val, name):
	"""return printable representation of time field"""
	if val is None: return "%s=None" % name
	if val == "*": return "%s=*" % name
	ranges = []
	for v in val:
	    if v[0] == v[1]:
		ranges.append("%02d:%02d" % (v[0]/60, v[0]%60))
	    else:
		ranges.append("%02d:%02d-%02d:%02d" %
			      (v[0]/60, v[0]%60, v[1]/60, v[1]%60))
	return "%s=%s" % (name, string.join(ranges, "/"))

    def wrepr(self, val, name):
	"""return printable representation of weekday field"""
	if val is None: return "%s=None" % name
	if val == "*": return "%s=*" % name
	ranges = []
	wkdays = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
	for v in val:
	    ranges.append("%s" % (wkdays[v[0]]))
	return "%s=%s" % (name, string.join(ranges, "/"))

    def __repr__(self):
	r = []
	r.append(self.frepr(self.year, "yy"))
	r.append(self.frepr(self.month, "mm"))
	r.append(self.frepr(self.day, "dd"))
	r.append(self.trepr(self.time, "hhmm"))
	r.append(self.wrepr(self.weekday, "wkdays"))
	return "<%s>" % string.join(r, ",")

    def __str__(self):
	return repr(self)

def test():
    # MWF 1-3pm
    r1 = Recurrence()
    r1.set_weekday(0)
    r1.add_weekday(2)
    r1.add_weekday(4)
    r1.set_hhmm_range(13, 00, 15, 00)
    print "r1:", r1

    r2 = Recurrence()
    r2.set_timetuple((1990, 9, 24))
    print "r2:", r2

    print "r1 intersect r2:", r1.intersect(r2)

    # TTh 2-4pm
    r3 = Recurrence()
    r3.set_weekday(1)
    r3.add_weekday(3)
    r3.set_hhmm_range(14, 00, 16, 00)
    print "r3:", r3

    print "r1 intersect r3:", r1.intersect(r3)

    start = DateTime.DateTime(1990, 9, 24)
    end = DateTime.DateTime(1990, 10, 13)
    step = DateTime.TimeDelta(hours=13)
    result = r1.enumerate(start, end, step)
    print "(enumerate) dates between", start, "&", end,
    print "(step %s) covered by r1:" % step
    for r in result: print "  ", r

    list = []
    s = start + 0
    while s <= end:
	list.append(s)
	s = s + step
    result = r1.filter(list)
    print "(filter) dates between", start, "&", end,
    print "(step %s) covered by r1:" % step
    for r in result: print "  ", r

    step = DateTime.TimeDelta(hours=1)
    result = r1.enumerate(start, end, step)
    print "dates between", start, "&", end, "(step %s) covered by r1:" % step
    for r in result: print "  ", r

    print "timing intersection test:"
    t = time.clock()
    for i in range(1000):
	x = r1.intersect(r2)
	x = r1.intersect(r3)
    print "%.4f seconds per intersection" % ((time.clock() - t)/2000)

if __name__ == "__main__": test()

