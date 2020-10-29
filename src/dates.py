# -*- coding: iso-8859-1 -*-

from calendar import month_name, day_name, mdays, month_abbr, day_abbr, isleap
import time
from types import *

class error(Exception): pass

_one_day = 24*60*60
month_num = {'jan':1, 'feb':2, 'mar':3, 'apr':4,
             'may':5, 'jun':6, 'jul':7, 'aug':8,
             'sep':9, 'oct':10, 'nov':11, 'dec':12,
             'january':1, 'february':2, 'march':3, 'april':4,
             'may':5, 'june':6, 'july':7, 'august':8,
             'september':9, 'october':10, 'november':11, 'december':12,
             'jan.':1, 'feb.':2, 'mar.':3, 'apr.':4,
             'may.':5, 'jun.':6, 'jul.':7, 'aug.':8,
             'sep.':9, 'oct.':10, 'nov.':11, 'dec.':12,
             'sept.':9, 'sept':9,
             # someone keeps submitting dates with september spelled wrong...
             'septmber':9,
             # italian ...
             'gennaio':1, 'febbraio':2, 'marzo':3,
             'aprile':4, 'maggio':5, 'giugno':6,
             'luglio':7, 'agosto':8, 'settembre':9,
             'ottobre':10, 'novembre':11, 'dicembre':12,
             # dutch ...
             'januari':1, 'februari':2, 'maart':3, 'mei':5,
             'juni':6, 'juli':7, 'augustus':8, 'oktober':10,
             # french ...
             'marche': 3, "avril": 4, "janvier": 1, "février": 2,
             "juin": 6, "juillet": 7, "août": 8, "septembre": 9,
             "octobre": 10, "novembre": 11, "décembre": 12, "mai": 5,
             # spanish ...
             "marzo": 3, "abril": 4, "enero": 1, "febrero": 2,
             "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
             "octubre": 10, "noviembre": 11, "diciembre": 12, "mayo": 5,
             # german ...
             "märz": 3, "januars": 1, "februar": 2,
             "juni": 6, "juli": 7, "dezember": 12,
             # portuguese ...
             "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
             "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
             "outubro": 10, "novembro": 11, "dezembro": 12,
             # swedish ...
             "jan":  1, "januari": 1,
             "feb":  2, "februari": 2,
             "mar":  3, "mars": 3,
             "apr":  4, "april": 4,
             "maj":  5, "maj": 5,
             "jun":  6, "juni": 6,
             "jul":  7, "juli": 7,
             "aug":  8, "augusti": 8,
             "sep":  9, "september": 9,
             "okt": 10, "oktober": 10,
             "nov": 11, "november": 11,
             "dec": 12, "december": 12,
             # norwegian ...
             "januar": 1,
             "februar": 2,
             "mars": 3,
             "april": 4,
             "mai": 5,
             "juni": 6,
             "juli": 7,
             "august": 8,
             "september": 9,
             "oktober": 10,
             "november": 11,
             "desember": 12,
             # finnish ...
             "tammikuu": 1,
             "helmikuu": 2,
             "maaliskuu": 3,
             "huhtikuu": 4,
             "toukokuu": 5,
             "kesäkuu": 6,
             "heinäkuu": 7,
             "kesakuu": 6,
             "heinakuu": 7,
             "elokuu": 8,
             "syyskuu": 9,
             "lokakuu": 10,
             "marraskuu": 11,
             "joulokuu": 12,
             }

weekdays = {'mon':0, 'tue':0, 'wed':0, 'thu':0, 'fri':0, 'sat':0, 'sun':0,
            'monday':0, 'tuesday':0, 'wednesday':0, 'thursday':0,
            'friday':0, 'saturday':0, 'sunday':0}

leap_mdays = mdays[:2] + [29] + mdays[3:]

# force regex build on first call...
_euro1 = _euro2 = _euro3 = _euro4 = None
_amer1 = _amer2 = _amer3 = _amer4 = None
_num0 = _num1 = _num2 = _num3 = _num4 = _num5 = _days_from_now = None
_month1 = _month2 = _iso8601 = None

_debug = 0

def guess_year(year):
    # this is obviously a punt on two-digit years...
    if 50 < year < 100:
        year = 1900 + year
    elif year <= 50:
        year = 2000 + year
    return year

def parse_date(date):

    global _euro1, _euro2, _euro3, _euro4
    global _amer1, _amer2, _amer3, _amer4
    global _num0, _num1, _num2, _num3, _num4, _num5, _days_from_now
    global _month1, _month2, _iso8601

    if _euro1 == None:
        sp = '[ \t]*'
        hardsp = '[ \t]+'
        to = '(-|to|through|thru)' + sp
        sday = '(?P<sd>0*[0-3]?[0-9])(th|rd|st|nd)?' + sp
        eday = '(?P<ed>0*[0-3]?[0-9])(th|rd|st|nd)?' + sp
        opteday = '(' + to + eday + ')?'
        smonth = '(?P<sm>[a-zéûäç]+\.?)' + sp
        emonth = '(?P<em>[a-zéûäç]+\.?)' + sp
        commaorsp = '(' + ',' + sp + '|' + hardsp + ')' 
        syear = '(?P<sy>[0-9]+)' + sp
        commaoptsyear = '(' + commaorsp + syear + ')?'
        eyear = '(?P<ey>[0-9]+)' + sp
        commaopteyear = '(' + commaorsp + eyear + ')?'

        # numeric thingies
        sep = '[-/]'
        nsmonth = '(?P<sm>0*[0-9]|1[012])'
        nemonth = '(?P<em>0*[0-9]|1[012])'
        nsday = '(?P<sd>0*[0-9]|[12][0-9]|3[01])'
        neday = '(?P<ed>0*[0-9]|[12][0-9]|3[01])'
        nsyr = '(?P<sy>[0-9]+)'
        neyr = '(?P<ey>[0-9]+)'
        optnsyr = '(%s%s)?' % (sep, nsyr)
        optneyr = '(%s%s)?' % (sep, neyr)

        import re
        # start date only, Euro format - 12 May 1995
        _euro1 = re.compile(sday + smonth + commaoptsyear + '$', re.I)
        # start and end date, Euro format, same month - 12-13 May 1995
        _euro2 = re.compile(sday + to + eday + smonth + commaoptsyear + '$',
                            re.I)
        # start and end date, Euro format, different month, same year
        _euro3 = re.compile(sday + smonth + to +
                            eday + emonth + commaoptsyear + '$', re.I)
        # start and end date, Euro format, different year - 31 December 1995 - 1 January 1996
        _euro4 = re.compile(sday + smonth + commaorsp + syear + to +
                            eday + emonth + commaorsp + eyear + '$', re.I)

        # start date only, American format, comma optionally separates day and year - May 12, 1995
        _amer1 = re.compile(smonth + sday + commaoptsyear + '$', re.I)
        # start and end date, American format, same month - May 12-13, 1995
        _amer2 = re.compile(smonth + sday + to + eday + commaoptsyear + '$',
                            re.I)
        # start and end date, American format, different month, same year
        _amer3 = re.compile(smonth + sday + to +
                            emonth + eday + commaoptsyear + '$', re.I)
        # start and end date, American format, different year
        _amer4 = re.compile(smonth + sday + commaorsp + syear + to +
                            emonth + eday + commaorsp + eyear + '$', re.I)

        # year only
        _num0 = re.compile(nsyr + '$')
        # start date, MM/DD or MM/DD/YY
        _num1 = re.compile(nsmonth + sep + nsday + optnsyr + '$')
        # start and end date, MM/DD/YY-MM/DD/YY or MM/DD-MM/DD
        _num2 = re.compile(nsmonth + sep + nsday + optnsyr + sp + to +
                           nemonth + sep + neday + optneyr + '$')
        # start date, MM/YY
        _num3 = re.compile(nsmonth + sep + nsyr + '$')

        # start date, MM/DD YYYY
        _num4 = re.compile(nsmonth + sep + nsday + opteday +
                           hardsp + syear + '$')

        # start and ed date, MM/DD-DD
        _num5 = re.compile(nsmonth + '/' + nsday + '-' + eday + '$')

        _iso8601 = re.compile(nsyr + '-' + nsmonth + '-' + nsday + '$')

        # XXX days from today
        _days_from_now = re.compile('[-+] *([0-9]+)( *(day|week|month)s?)?',
                                    re.I)

        _month1 = re.compile(smonth + commaoptsyear + '$', re.I)
        _month2 = re.compile(smonth + commaoptsyear + to +
                             emonth + commaopteyear + '$', re.I)

    s = date.lower().strip()

    start = end = 0

    now = time.time()
    year = time.gmtime(now)[0]

    if s == 'today':
        start = end = time.mktime(time.gmtime(now)[0:3]+(0,)*6)
        if _debug > 1: print 'today matched'
        return start, end

    if s in ['new years eve', "new year's eve"]:
        start = end = time.mktime((year, 12, 31)+(0,)*6)
        if _debug > 1: print 'new years eve matched'
        return start, end

    if s in ['christmas', "xmas"]:
        start = end = time.mktime((year, 12, 25)+(0,)*6)
        if _debug > 1: print 'christmas matched'
        return start, end

    if s == 'tomorrow':
        start = end = time.mktime(time.gmtime(now+_one_day)[0:3]+(0,)*6)
        if _debug > 1: print 'tomorrow matched'
        return start, end

    try:
        result = parse_iso(s)
        if result is not None:
            return result

        result = parse_num0(s)
        if result is not None:
            return result

        # must be checked before the other numeric dates which involve 'sep'
        # since this uses '/' and '-' to mean different things
        result = parse_num5(s)
        if result is not None:
            return result

        result = parse_num2(s)
        if result is not None:
            return result

        result = parse_num4(s)
        if result is not None:
            return result

        # note that there is an ambiguity between _num1 and num3.  we
        # resolve it by searching for mm/dd first.

        result = parse_num1(s)
        if result is not None:
            return result

        result = parse_num3(s)
        if result is not None:
            return result

        result = parse_amer1(s)
        if result is not None:
            return result

        result = parse_amer2(s)
        if result is not None:
            return result

        result = parse_amer3(s)
        if result is not None:
            return result

        result = parse_amer4(s)
        if result is not None:
            return result

        result = parse_days_from_now(s)
        if result is not None:
            return result

        result = parse_euro1(s)
        if result is not None:
            return result

        result = parse_euro2(s)
        if result is not None:
            return result

        result = parse_euro3(s)
        if result is not None:
            return result

        result = parse_euro4(s)
        if result is not None:
            return result

        result = parse_month1(s)
        if result is not None:
            return result

        result = parse_month2(s)
        if result is not None:
            return result

        raise error, 'Date not in an understood format: %s' % s

    except ValueError:
        raise error, 'Date Format Error: %s' % s

    except KeyError:
        raise error, 'Date Format Error: %s - check spelling of months' % s

    except OverflowError:
        if _debug > 1: print 'OverflowError, probably in mktime()'
        raise error, 'Numeric Overflow: %s - check range of numbers' % s

def parse_iso(s):
    mat = _iso8601.match(s)
    if mat is None:
        return None
    year = guess_year(int(mat.group('sy')))
    smonth = int(mat.group('sm'))
    sday = int(mat.group('sd'))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    if (1 > sday or
        smonth < len(_mdays) and sday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % s
    start = end = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    return start, end

def parse_num0(s):
    mat = _num0.match(s)
    if mat is None:
        return None
    smonth = 1 ; sday = 1
    emonth = 12 ; eday = 31
    year = guess_year(int(mat.group('sy')))
    start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((year, emonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num0 matched'
    return start, end

def parse_num2(s):
    mat = _num2.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    smonth = int(mat.group('sm'))
    emonth = int(mat.group('em'))
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    if (1 > sday or
        smonth < len(_mdays) and sday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % s
    start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    if mat.group('ey'):
        year = guess_year(int(mat.group('ey')))
        if isleap(year): _mdays = leap_mdays
        else: _mdays = mdays
    if (1 > sday or
        smonth < len(_mdays) and sday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % s
    end = time.mktime((year, emonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num2 matched'
    return start, end

def parse_num1(s):
    # match mm/dd
    mat = _num1.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    smonth = int(mat.group('sm'))
    sday = int(mat.group('sd'))
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
        if isleap(year): _mdays = leap_mdays
        else: _mdays = mdays
    else:
        # assume day and month given
        if isleap(year): _mdays = leap_mdays
        else: _mdays = mdays

    if (1 > sday or
        smonth < len(_mdays) and sday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % s
    start = end = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num1 matched'
    return start, end

def parse_num3(s):
    # match mm/yy
    mat = _num3.match(s)
    if mat is None:
        return None
    smonth = int(mat.group('sm'))
    syear = int(mat.group('sy'))
    if isleap(syear): _mdays = leap_mdays
    else: _mdays = mdays
    sday = 1
    eday = _mdays[smonth]
    start = time.mktime((syear, smonth, sday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((syear, smonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num3 matched'
    return start, end

def parse_num4(s):
    # match mm/dd yyyy
    mat = _num4.match(s)
    if mat is None:
        return None
    smonth = int(mat.group('sm'))
    sday = int(mat.group('sd'))
    try:
        eday = int(mat.group('ed'))
    except ValueError:
        eday = sday
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
        if isleap(year): _mdays = leap_mdays
        else: _mdays = mdays

    if (1 > sday or
        smonth < len(_mdays) and sday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % date
    if (1 > eday or
        smonth < len(_mdays) and eday > _mdays[smonth]):
        raise error, 'Day of the month out of range: %s' % date
    start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((year, smonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num4 matched'
    return start, end

def parse_num5(s):
    mat = _num5.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    smonth = int(mat.group('sm'))
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((year, smonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'num5 matched'
    return start, end
    
def parse_amer1(s):
    mat = _amer1.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    try:
        sday = eday = int(mat.group('sd'))
    except TypeError:
        sday = 1
        eday = _mdays[smonth]
    if 1 <= sday <= _mdays[smonth]:
        if _debug > 1:
            print 'amer1 matched', (year, smonth, sday, eday)
        start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((year, smonth, eday, 0, 0, 0, 0, 0, 0))
        return start, end
    elif mat.group('sy'):
        raise error, 'Day of the month out of range: %s' % s

def parse_amer2(s):
    mat = _amer2.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    if (1 <= sday <= _mdays[smonth] and
        1 <= eday <= _mdays[smonth]):
        start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((year, smonth, eday, 0, 0, 0, 0, 0, 0))
        if _debug > 1: print 'amer2 matched'
        return start, end
    else:
        raise error, 'Day of the month out of range: %s' % s

def parse_amer3(s):
    mat = _amer3.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    emonth = month_num[mat.group('em').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    if (1 <= sday <= _mdays[smonth] and
        1 <= eday <= _mdays[emonth]):
        start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((year, emonth, eday, 0, 0, 0, 0, 0, 0))
        if _debug > 1: print 'amer3 matched'
        return start, end
    else:
        raise error, 'Day of the month out of range: %s' % s

def parse_amer4(s):
    mat = _amer4.match(s)
    if mat is None:
        return None
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    emonth = month_num[mat.group('em').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))

    syear = int(mat.group('sy'))
    if isleap(syear): _mdays = leap_mdays
    else: _mdays = mdays
    if 1 <= sday <= mdays[smonth]:
        start = time.mktime((syear, smonth, sday, 0, 0, 0, 0, 0, 0))
    else:
        raise error, 'Day of the month out of range: %s' % s

    eyear = int(mat.group('ey'))
    if isleap(eyear): _mdays = leap_mdays
    if 1 <= eday <= _mdays[emonth]:
        end = time.mktime((eyear, emonth, eday, 0, 0, 0, 0, 0, 0))
    else:
        raise error, 'Day of the month out of range: %s' % s
    if _debug > 1: print 'amer4 matched'
    return start, end

def parse_days_from_now(s):
    mat = _days_from_now.match(s)
    if mat is None:
        return None
    sign = 1
    if s[0] == '-': sign = -1
    howmany = int(mat.group(1))
    units = mat.group(3)
    if units == 'week':
        howmany = howmany * 7
    elif units == 'month':
        howmany = howmany * 30

    start = time.time()
    end = start + sign*howmany*24*60*60
    if start > end:
        start, end = end, start
    if _debug > 1: print 'relative date matched'
    return start, end

def parse_euro1(s):
    mat = _euro1.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    if 1 <= sday <= _mdays[smonth]:
        start = end = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        if _debug > 1: print 'euro1 matched'
        return start, end
    else:
        raise error, 'Day of the month out of range: %s' % s

def parse_euro2(s):
    mat = _euro2.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    if (1 <= sday <= _mdays[smonth] and
        1 <= eday <= _mdays[smonth]):
        start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((year, smonth, eday, 0, 0, 0, 0, 0, 0))
        if _debug > 1: print 'euro2 matched'
        return start, end
    else:
        raise error, 'Day of the month out of range: %s' % s

def parse_euro3(s):
    mat = _euro3.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    if isleap(year): _mdays = leap_mdays
    else: _mdays = mdays
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    emonth = month_num[mat.group('em').encode("iso-8859-1")]
    sday = int(mat.group('sd'))
    eday = int(mat.group('ed'))
    if (1 <= sday <= _mdays[smonth] and
        1 <= eday <= _mdays[emonth]):
        start = time.mktime((year, smonth, sday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((year, emonth, eday, 0, 0, 0, 0, 0, 0))
        if _debug > 1: print 'euro3 matched'
        return start, end
    else:
        raise error, 'Day of the month out of range: %s' % s

def parse_euro4(s):
    mat = _euro4.match(s)
    if mat is None:
        return None
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    emonth = month_num[mat.group('em').encode("iso-8859-1")]

    sday = int(mat.group('sd'))
    syear = guess_year(int(mat.group('sy')))
    if isleap(syear): _mdays = leap_mdays
    else: _mdays = mdays
    if 1 > sday or sday > _mdays[smonth]:
        raise error, 'Day of the month out of range: %s' % s

    eday = int(mat.group('ed'))
    eyear = guess_year(int(mat.group('ey')))
    if isleap(eyear): _mdays = leap_mdays
    else: _mdays = mdays
    if 1 > eday or eday > _mdays[emonth]:
        raise error, 'Day of the month out of range: %s' % s

    start = time.mktime((syear, smonth, sday, 0, 0, 0, 0, 0, 0))
    end = time.mktime((eyear, emonth, eday, 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'euro4 matched'
    return start, end

def parse_month1(s):
    mat = _month1.match(s)
    year = time.gmtime(time.time())[0]
    if mat is None:
        return None
    if mat.group('sy'):
        year = guess_year(int(mat.group('sy')))
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    start = time.mktime((year, smonth, 1, 0, 0, 0, 0, 0, 0))
    end = time.mktime((year, smonth, mdays[smonth], 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'month1 matched'
    return start, end

def parse_month2(s):
    mat = _month2.match(s)
    if mat is None:
        return None
    syear = eyear = None
    if mat.group('ey'):
        eyear = guess_year(int(mat.group('ey')))
    if mat.group('sy'):
        syear = guess_year(int(mat.group('sy')))
    if syear is None:
        if eyear is not None:
            syear = eyear
        else:
            syear = eyear = time.gmtime(time.time())[0]
    elif eyear is None:
        if syear is not None:
            eyear = syear
    smonth = month_num[mat.group('sm').encode("iso-8859-1")]
    emonth = month_num[mat.group('em').encode("iso-8859-1")]
    start = time.mktime((syear, smonth, 1, 0, 0, 0, 0, 0, 0))
    end = time.mktime((eyear, emonth, mdays[emonth], 0, 0, 0, 0, 0, 0))
    if _debug > 1: print 'month2 matched'
    return start, end

def ascdate(start, end = 0, format = '%A, %B %e, %Y', connect = ' to '):
    sday = time.gmtime(start)

    if not end or (end == start):
        return time.strftime(format, sday)
    else:
        eday = time.gmtime(end)
        return '%s%s%s' % (time.strftime(format, sday), connect,
                           time.strftime(format, eday))
        
def date_range(start, end):
    """generate range of dates from start to end, inclusive"""
    
    # new code assumes dates in iso8601 format (e.g. "2000-02-09")
    sy, sm, sd = map(int, start.split("-"))
    ey, em, ed = map(int, end.split("-"))
    start = time.mktime((sy, sm, sd) + (0,)*6)
    end = time.mktime((ey, em, ed) + (0,)*6)

    result = range(start, end+_one_day, _one_day)

    return map(iso8601, result)

def iso8601(t):
    return "%04d-%02d-%02d" % time.gmtime(t)[0:3]

def parse_iso8601(t):
    for format in ("%Y-%m-%dT%H:%M:%S",
                   "%Y-%m-%d %H:%M:%S",
                   "%Y-%m-%d:%H:%M:%S",
                   "%Y-%m-%d"):
        try:
            return time.strptime(t, format)
        except ValueError:
            pass
    raise ValueError, "unrecognized ISO 8601 date/time format: %s" % t
        
### Time class and associated bits and pieces...

# valid units of representation
seconds = 1.0
minutes = seconds * 60
hours = minutes * 60
days = hours * 24
weeks = days * 7

# map units for printing
_umap = { seconds:'seconds', minutes:'minutes', hours:'hours', days:'days',
          weeks:'weeks'}

_numtypes = (type(1), type(1L), type(1.0))

class Time:

    def __init__(self, val = 0, format = '%a, %b %d, %Y', units = seconds):
        if type(val) == TupleType:
            # time tuple as returned by time.gmtime()
            # pad if necessary to nine elements
            val = map(None, val)
            while len(val) < 9: val.append(0)
            val = tuple(val)
            val = time.mktime(val) / units

        self.value = val
        self._units = units
        self.format = format

    def __cmp__(self, other):
        if type(other) in _numtypes: oval = other
        else: oval = other.value * other._units
        if self.value * self._units < oval:
            return -1
        if self.value * self._units > oval:
            return 1
        return 0

    def __repr__(self):
        return "'%s'" % str(self)

    def __str__(self):
        ustr = _umap[self._units]
        val = self.value
        return '%f %s' % (val, ustr)

    def __add__(self, other):
        if type(other) in _numtypes: oval = other
        else: oval = other.value * other._units
        d = Time(self.value * self._units + oval, self.format, self._units)
        return d

    __radd__ = __add__

    def __sub__(self, other):
        if type(other) in _numtypes: oval = other
        else: oval = other.value * other._units
        d = Time(self.value * self._units - oval, self.format)
        d.units(self._units)
        return d

    def __rsub__(self, other):
        return other - self

    def __mul__(self, other):
        if type(other) in _numtypes:
            t = Time(self.value * self._units * other, self.format)
            t.units(self._units)
            return t
        else:
            raise TypeError, "multiplication of two times is undefined"

    __rmul__ = __mul__

    def __nonzero__(self):
        return (self.value * self._units != 0.0)

    def __div__(self, other):
        if type(other) in _numtypes:
            t = Time(self.value * self._units / other, self.format)
            t.units(self._units)
            return t
        else:
            return (self.value * self._units) / (other.value * other._units)

    def __rdiv__(self, other):
        return other / self

    def __mod__(self, other):
        if type(other) in _numtypes:
            t = Time(self.value * self._units % other, self.format)
            t.units(self._units)
            return t
        else:
            return (self.value * self._units) % (other.value * other._units)

    def __divmod__(self, other):
        return (self/other), (self % other)

    def __neg__(self):
        return Time(-self.value, self.format, self._units)

    def __pos__(self):
        return Time(self.value, self.format, self._units)

    def __abs__(self):
        return Time(abs(self.value), self.format, self._units)

    def __invert__(self):
        return Time(~self.value, self.format, self._units)

    def __coerce__(self, other):
        if type(other) in _numtypes or type(other) == type(self):
            return self, other
        return None

    def __int__(self):
        return int(self.value)

    def __long__(self):
        return long(self.value)

    def __float__(self):
        return float(self.value)

    def units(self, u):
        self.value = self.value * float(self._units) / u
        self._units = u

    def seconds(self):
        return self.value * self._units

    def minutes(self):
        return self.seconds() / minutes

    def hours(self):
        return self.seconds() / hours

    def days(self):
        return self.seconds() / days

    def __getitem__(self, index):
        return time.gmtime(self.seconds())[index]

    def year(self): return self[0]
    def month(self): return self[1]
    def day(self): return self[2]
    def hour(self): return self[3]
    def minute(self): return self[4]
    def second(self): return self[5]
    def dow(self): return self[6]
    def julian(self): return self[7]
    
    def weekday(self): return day_name[self[6]]
    def wkday(self): return day_abbr[self[6]]
    def month_name(self): return month_name[self[1]]
    def month_abbr(self): return month_abbr[self[1]]

    def text(self):
        return time.strftime(self.format, time.gmtime(self.seconds()))

def _time_test():
    t = time.time()
    today = Time(t)
    print 'Today in seconds:', today
    today.units(minutes)
    print 'Today in minutes:', today
    print 'Today =?= time.time():', today == t
    print 'Today + 5 seconds (int):', today + 5
    print 'Today + 5 minutes (int):', today + 5*60
    print "Today's month: (%d, %s, %s)" % (today.month(), today.month_name(),
                                          today.month_abbr())
    print "Today's dayofweek: (%d, %s, %s)" % (today.dow(), today.weekday(),
                                              today.wkday())
    one_day = Time(1, '%a, %b %d, %Y', days)
    tomorrow = today + one_day
    yesterday = today - one_day
    tomorrow.units(days)
    yesterday.units(hours)
    print yesterday, today, tomorrow

    dec_31_1995 = Time((1995, 12, 31), '%a, %b %d, %Y', days)
    print 'December 31, 1995:', dec_31_1995
    ten_days_later = dec_31_1995 + Time(10, '%a, %b %d, %Y', days)
    print '10 days later:', ten_days_later, time.gmtime(ten_days_later.seconds())
    dec_31_1995.units(minutes)
    today.units(days)
    print 'Today minus 12/31/1995 in days: %6.2f' % (today - dec_31_1995)
    today.units(weeks)
    print 'Today minus 12/31/1995 in weeks: %5.2f' % (today - dec_31_1995)

    four_days = one_day * 4
    print 'Four days, one day:', four_days, one_day
    print 'Four days / one day:', four_days / one_day

    print '(yesterday + one_day) / today:', (yesterday + one_day) / today
    print '(tomorrow - one_day) / today:', (tomorrow - one_day) / today
    print 'tomorrow - yesterday:', tomorrow - yesterday

def _dates_test():
    year = time.gmtime(time.time())[0]
    zeros = (0,)*6
    mktime = time.mktime
    tests = [
        ('10th June 1995',
         (time.mktime((1995, 6, 10)+zeros),
          time.mktime((1995, 6, 10)+zeros))),
        ('0002 June 2000',
         (time.mktime((2000, 6, 2)+zeros),
          time.mktime((2000, 6, 2)+zeros))),
        ('12 August, 1995',
         (time.mktime((1995, 8, 12)+zeros),
          time.mktime((1995, 8, 12)+zeros))),
        ('12 August,1995',
         (time.mktime((1995, 8, 12)+zeros),
          time.mktime((1995, 8, 12)+zeros))),
        ('December 31, 1995-January 1, 1996',
         (time.mktime((1995, 12, 31)+zeros),
          time.mktime((1996, 1, 1)+zeros))),
        ('December31,1995-January1,1996',
         (time.mktime((1995, 12, 31)+zeros),
          time.mktime((1996, 1, 1)+zeros))),
        ('December 31,1995 - January 1,1996',
         (time.mktime((1995, 12, 31)+zeros),
          time.mktime((1996, 1, 1)+zeros))),
        ('30 May',
         (time.mktime((year, 5, 30)+zeros),
          time.mktime((year, 5, 30)+zeros))),
        ('30-31 May',
         (time.mktime((year, 5, 30)+zeros),
          time.mktime((year, 5, 31)+zeros))),
        ('31 May-1 June',
         (time.mktime((year, 5, 31)+zeros),
          time.mktime((year, 6, 1)+zeros))),
        ('May 30',
         (time.mktime((year, 5, 30)+zeros),
          time.mktime((year, 5, 30)+zeros))),
        ('5 Mayo',
         (time.mktime((year, 5, 5)+zeros),
          time.mktime((year, 5, 5)+zeros))),
        ('12 to 13 August 1995',
         (time.mktime((1995, 8, 12)+zeros),
          time.mktime((1995, 8, 13)+zeros))),
        (u'février 28 to Août 1, 1995',
         (time.mktime((1995, 2, 28)+zeros),
          time.mktime((1995, 8, 1)+zeros))),
        ]

    fail = 0
    for dstr, desired in tests:
        if _debug: print "%s:" % dstr,
        try:
            result = parse_date(dstr)
            if result != desired:
                if _debug: print 'Failure:',
                else: print 'Failure (%s):' % dstr,
                print (time.gmtime(result[0])[0:3],
                       time.gmtime(result[1])[0:3]),
                print '!=',
                print (time.gmtime(desired[0])[0:3],
                       time.gmtime(desired[1])[0:3]),
                fail = fail + 1
            else:
                if _debug: print "passed"
        except error, msg:
            print 'Date Parsing Failure:', repr(msg)
            fail = fail + 1

    if not fail:
        print 'All', len(tests), 'date parsing tests passed'
    else:
        print fail, ('test%s failed.' % (fail > 1 and "s" or ""))
        print len(tests)-fail, 'tests passed.'

if __name__ == '__main__':
    import unittest

    class ISO8601TestCase(unittest.TestCase):
        def test_date_time(self):
            self.assertEqual(parse_iso8601("2003-02-28")[0:6],
                             (2003, 2, 28, 0, 0, 0))
            self.assertEqual(parse_iso8601("2003-02-28T12:13:14")[0:6],
                             (2003, 2, 28, 12, 13, 14))
            self.assertEqual(parse_iso8601("2003-02-28 12:13:14")[0:6],
                             (2003, 2, 28, 12, 13, 14))
            self.assertEqual(parse_iso8601("2003-02-28:12:13:14")[0:6],
                             (2003, 2, 28, 12, 13, 14))

        def test_raise(self):
            self.assertRaises(ValueError, parse_iso8601, "12:13:14")

    class DateTestCase(unittest.TestCase):
        zeros = (0,)*6

        def test_iso8601(self):
            self.assertEqual(parse_date('2005-2-28'),
                             (time.mktime((2005, 2, 28)+self.zeros),
                              time.mktime((2005, 2, 28)+self.zeros)))
            self.assertEqual(parse_date('2005-02-28'),
                             (time.mktime((2005, 2, 28)+self.zeros),
                              time.mktime((2005, 2, 28)+self.zeros)))
            self.assertEqual(parse_date('1996-2-29'),
                             (time.mktime((1996, 2, 29)+self.zeros),
                              time.mktime((1996, 2, 29)+self.zeros)))
            self.assertEqual(parse_date('1997-12-31'),
                             (time.mktime((1997, 12, 31)+self.zeros),
                              time.mktime((1997, 12, 31)+self.zeros)))

            self.assertEqual(parse_date('97-12-31'),
                             (time.mktime((1997, 12, 31)+self.zeros),
                              time.mktime((1997, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('05-12-31'),
                             (time.mktime((2005, 12, 31)+self.zeros),
                              time.mktime((2005, 12, 31)+self.zeros)))

        def test_num0(self):
            self.assertEqual(parse_date('2005'),
                             (time.mktime((2005, 1, 1)+self.zeros),
                              time.mktime((2005, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('2005 '),
                             (time.mktime((2005, 1, 1)+self.zeros),
                              time.mktime((2005, 12, 31)+self.zeros)))

        def test_num2(self):
            self.assertEqual(parse_date('12-31-95 to 1/1/96'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('12-31-95 to 1-1-96'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('8/20/95 to 8/30/95'),
                             (time.mktime((1995, 8, 20)+self.zeros),
                              time.mktime((1995, 8, 30)+self.zeros)))
            self.assertEqual(parse_date('8/20/95 to 8/30'),
                             (time.mktime((1995, 8, 20)+self.zeros),
                              time.mktime((1995, 8, 30)+self.zeros)))
            self.assertEqual(parse_date('12-31-95-1/1/96'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('12-31-95 thru 1-12-96'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 12)+self.zeros)))
            self.assertEqual(parse_date('8/20/95-8/30/95'),
                             (time.mktime((1995, 8, 20)+self.zeros),
                              time.mktime((1995, 8, 30)+self.zeros)))
            self.assertEqual(parse_date('8/20/95-8/30/95 '),
                             (time.mktime((1995, 8, 20)+self.zeros),
                              time.mktime((1995, 8, 30)+self.zeros)))
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('8/20-8/30'),
                             (time.mktime((year, 8, 20)+self.zeros),
                              time.mktime((year, 8, 30)+self.zeros)))

        def test_num1(self):
            self.assertEqual(parse_date('12-31-95'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('12-31-1998'),
                             (time.mktime((1998, 12, 31)+self.zeros),
                              time.mktime((1998, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('12-31-05'),
                             (time.mktime((2005, 12, 31)+self.zeros),
                              time.mktime((2005, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('12/31/95'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('12/31'),
                             (time.mktime((year, 12, 31)+self.zeros),
                              time.mktime((year, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('1/31'),
                             (time.mktime((year, 1, 31)+self.zeros),
                              time.mktime((year, 1, 31)+self.zeros)))
            self.assertEqual(parse_date('1/31 '),
                             (time.mktime((year, 1, 31)+self.zeros),
                              time.mktime((year, 1, 31)+self.zeros)))
            self.assertEqual(parse_date('12/94'),
                             (time.mktime((1994, 12, 1)+self.zeros),
                              time.mktime((1994, 12, 31)+self.zeros)))

        def test_special(self):
            self.assertEqual(parse_date('Today'),
                             (time.mktime(time.gmtime(time.time())[:3]+
                                          self.zeros),
                              time.mktime(time.gmtime(time.time())[:3]+
                                          self.zeros)))
            self.assertEqual(parse_date('tomorrow'),
                             (time.mktime(time.gmtime(time.time()+_one_day)[:3]
                                          +self.zeros),
                              time.mktime(time.gmtime(time.time()+_one_day)[:3]
                                          +self.zeros)))
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('xmas'),
                             (time.mktime((year, 12, 25)+self.zeros),
                              time.mktime((year, 12, 25)+self.zeros)))
            self.assertEqual(parse_date('xmas '),
                             (time.mktime((year, 12, 25)+self.zeros),
                              time.mktime((year, 12, 25)+self.zeros)))
            self.assertEqual(parse_date(' xmas '),
                             (time.mktime((year, 12, 25)+self.zeros),
                              time.mktime((year, 12, 25)+self.zeros)))

        def test_num3(self):
            self.assertEqual(parse_date('12/95'),
                             (time.mktime((1995, 12, 1)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))
            self.assertEqual(parse_date(' 12/95 '),
                             (time.mktime((1995, 12, 1)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))

        def test_amer1(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('August 12th 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('August 12th 98'),
                             (time.mktime((1998, 8, 12)+self.zeros),
                              time.mktime((1998, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('August 12th, 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('August 12,1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('Aug. 12, 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('August12,1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 12)+self.zeros)))
            self.assertEqual(parse_date('August 13'),
                             (time.mktime((year, 8, 13)+self.zeros),
                              time.mktime((year, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('August 13 '),
                             (time.mktime((year, 8, 13)+self.zeros),
                              time.mktime((year, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('August 22nd'),
                             (time.mktime((year, 8, 22)+self.zeros),
                              time.mktime((year, 8, 22)+self.zeros)))

        def test_amer2(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('August 12-13, 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('August 12-13,1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('May 3rd - 31st'),
                             (time.mktime((year, 5, 3)+self.zeros),
                              time.mktime((year, 5, 31)+self.zeros)))

        def test_amer3(self):
            self.assertEqual(parse_date('August 31-September 1, 1995'),
                             (time.mktime((1995, 8, 31)+self.zeros),
                              time.mktime((1995, 9, 1)+self.zeros)))
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('May 31-June 1st'),
                             (time.mktime((year, 5, 31)+self.zeros),
                              time.mktime((year, 6, 1)+self.zeros)))
            self.assertEqual(parse_date('August 12 to 13, 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('August 12 to 13, 10'),
                             (time.mktime((2010, 8, 12)+self.zeros),
                              time.mktime((2010, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('August 12 to 13,1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 13)+self.zeros)))
            self.assertEqual(parse_date('May 31 to June 1'),
                             (time.mktime((year, 5, 31)+self.zeros),
                              time.mktime((year, 6, 1)+self.zeros)))

        def test_amer4(self):
            self.assertEqual(parse_date('December 31, 1995 to January 1, 1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('December31,1995 to January1,1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('december31,1995 to january1,1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('December 31,1995  to  January 1,1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))

        def test_days_from_now(self):
            target = int(time.time()+5*24*60*60)
            today = int(time.time())
            answer = parse_date('+5 days')
            answer = (int(answer[0]), int(answer[1]))
            self.assertEqual(answer, (today, target))

            target = int(time.time()-5*7*24*60*60)
            today = int(time.time())
            answer = parse_date('-5 weeks')
            answer = (int(answer[0]), int(answer[1]))
            self.assertEqual(answer, (target, today))

        def test_euro1(self):
            self.assertEqual(parse_date('1 Janeiro 1994'),
                             (time.mktime((1994, 1, 1)+self.zeros),
                              time.mktime((1994, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('1 Sept. 1995'),
                             (time.mktime((1995, 9, 1)+self.zeros),
                              time.mktime((1995, 9, 1)+self.zeros)))

        def test_euro2(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('30 to 31 May'),
                             (time.mktime((year, 5, 30)+self.zeros),
                              time.mktime((year, 5, 31)+self.zeros)))
            self.assertEqual(parse_date('12-13 August 1995'),
                             (time.mktime((1995, 8, 12)+self.zeros),
                              time.mktime((1995, 8, 13)+self.zeros)))

        def test_euro3(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('31 May to 1 June'),
                             (time.mktime((year, 5, 31)+self.zeros),
                              time.mktime((year, 6, 1)+self.zeros)))
            self.assertEqual(parse_date('31 May to 1 June 1995'),
                             (time.mktime((1995, 5, 31)+self.zeros),
                              time.mktime((1995, 6, 1)+self.zeros)))
            self.assertEqual(parse_date(u'février 28 to Août 1, 1995'),
                             (time.mktime((1995, 2, 28)+self.zeros),
                              time.mktime((1995, 8, 1)+self.zeros)))
            self.assertEqual(parse_date('31 May-1 June'),
                             (time.mktime((year, 5, 31)+self.zeros),
                              time.mktime((year, 6, 1)+self.zeros)))
            self.assertEqual(parse_date('31 May-1 June 1995'),
                             (time.mktime((1995, 5, 31)+self.zeros),
                              time.mktime((1995, 6, 1)+self.zeros)))
            self.assertEqual(parse_date(u'février 28-Août 1, 1995'),
                             (time.mktime((1995, 2, 28)+self.zeros),
                              time.mktime((1995, 8, 1)+self.zeros)))

        def test_euro4(self):
            self.assertEqual(parse_date('3 June 2000-31 December 2001'),
                             (time.mktime((2000, 6, 3)+self.zeros),
                              time.mktime((2001, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('31 December 1995 to 1 January,1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('31 December 1995-1 January,1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))
            self.assertEqual(parse_date('31 December 1995 to 1st January 1996'),
                             (time.mktime((1995, 12, 31)+self.zeros),
                              time.mktime((1996, 1, 1)+self.zeros)))

        def test_month1(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('December 1995'),
                             (time.mktime((1995, 12, 1)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('December,1995'),
                             (time.mktime((1995, 12, 1)+self.zeros),
                              time.mktime((1995, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('December'),
                             (time.mktime((year, 12, 1)+self.zeros),
                              time.mktime((year, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('december'),
                             (time.mktime((year, 12, 1)+self.zeros),
                              time.mktime((year, 12, 31)+self.zeros)))

        def test_month2(self):
            year = time.gmtime(time.time())[0]
            self.assertEqual(parse_date('august-December'),
                             (time.mktime((year, 8, 1)+self.zeros),
                              time.mktime((year, 12, 31)+self.zeros)))
            self.assertEqual(parse_date('August thru September, 1998'),
                             (time.mktime((1998, 8, 1)+self.zeros),
                              time.mktime((1998, 9, 30)+self.zeros)))
            self.assertEqual(parse_date('August 1995 through September, 1998'),
                             (time.mktime((1995, 8, 1)+self.zeros),
                              time.mktime((1998, 9, 30)+self.zeros)))

        def test_errors(self):
            self.assertRaises(error, parse_date, 'My 31 to June 1')
            self.assertRaises(error, parse_date, 'Wednesday')
            self.assertRaises(error, parse_date, '8/20th-8/30')
            self.assertRaises(error, parse_date, '05b-12-31')

    _time_test()
    _dates_test()

    unittest.main()
