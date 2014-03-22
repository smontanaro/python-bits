
"""cgivalidate.py - version 0.4 (9/30/99)

Works like cgi.py module, but allows the script writer (or form writer for
the Hidden* variants) to specify required and optional parameters as well as
type-checking functions for them.  See ValidatedFieldStorage,
HiddenFieldStorage and HiddenFileFieldStorage classes and test functions for
examples.

Author: Skip Montanaro (skip@mojam.com)

External interface:

    class ValidatedFieldStorage
    class HiddenFieldStorage
    class HiddenFileFieldStorage
    function checkint
    function checkfloat
    function checkdate
    exception ValidationError

"""

import cgi, UserDict, os, operator, string, sys, calendar
from types import *

ValidationError = 'Error validating CGI parameters'

class keydict(UserDict.UserDict):
    def __getitem__(self, key):
	try:
	    return self.data[key]
	except KeyError:
	    return key

# function to guard against client closing socket prematurely
# just give up if that happens
def _emit(s):
    try:
	sys.stdout.write(s)
    except IOError:
	sys.exit(1)

class ValidatedFieldStorage(cgi.FieldStorage):
    """Adds type checking to FieldStorage class.

    Example:

    form = cgivalidate.FieldStorage()
    form.add_required('n')
    form.add_required('amt', checkfloat)
    form.optional('age', checkint)
    form.set_parameter_map({'n': 'Employee Name',
			    'amt': 'FICA Witholding',
			    'age': 'Employee Age'})
    form.validate()
    """

    def __init__(self, fp=None, headers=None, outerboundary="",
		 environ=os.environ, keep_blank_values=None,
		 generate_error_page=1, log_errors=0):
	cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
				  environ, keep_blank_values)
	self._required = []
	self._optional = []
	self.generate_error_page = generate_error_page
	self.log_errors = log_errors
	self.param_map = keydict()

    def set_parameter_map(self, dict):
	self.param_map = keydict()
	map(operator.__setitem__, [self.param_map]*len(dict),
	    dict.keys(), dict.values())

    def clear(self):
	self._required = []
	self._optional = []

    def add_required(self, name, checkfunc=None, params=None):
	"""Identify one or more required CGI parameters.

	If the optional check function is given it will be called to
	validate the types and ranges of the parameters.  If params is
	given, it is a tuple of extra arguments for checkfunc

	The first parameter can be an individual CGI parameter name or a
	tuple of parameter names or tuples.  If a tuple is given, all
	elements listed at the top-level of the tuple must be given.  If any
	of the tuple's elements are themselves tuples, at least one of the
	elements of that tuple must be present.  Only the first of those
	parameter names will be passed to the check function.

	Now that you are thoroughly mystified, here is a simple example to
	clear things up.

	    form = cgivalidate.FieldStorage()
	    form.add_required(('name',
			       'addr',
			       'city', ('state', 'country'),
			       'postalcode'),
			       checkaddress)

	With the following parameters:
	    name:	Skip Montanaro
	    addr:	P.O. Box 196
	    city:	Rexford
	    state:	NY
	    country:	USA
	    postalcode:	12148-0196
        checkaddress would be called with a single tuple:

	    ('Skip Montanaro', 'P.O. Box 196', 'Rexford', 'NY', '12148-0196')

	The check function must expect a single argument having
	the same top-level structure as the name parameter.  If type
	checking fails, it must raise ValidationError with a descriptive
	second argument.
	"""
	self._required.append((name, checkfunc, params))

    def add_optional(self, name, checkfunc=None, params=None):
	"""Identify one or more optional CGI parameters.

	If the optional check function is given it will be called to
	validate the types and ranges of the parameters.

	The first parameter can be an individual CGI parameter name or a
	tuple of parameter names.  If a tuple is given, if any parameter names
	are given only the first found is checked.  The check function
        must expect a single argument having the same structure as the
	name parameter.  If type checking fails, the check function must
	raise ValidationError with a descriptive second argument.
	"""
	self._optional.append((name, checkfunc, params))

    def __repr__(self):
	"""Return printable representation."""
	return "ValidatedFieldStorage(%s, %s)" % (`self.name`, `self.value`)

    def make_required(self, name):
	if type(name) == StringType:
	    try:
		if type(self[name]) == ListType:
		    v = []
		    for e in self[name]:
			v.append(e.value)
		    return v
		else:
		    return self[name].value
	    except (AttributeError, KeyError):
		raise ValidationError, name
	elif type(name) == TupleType:
	    result = []
	    missing = []
	    for elt in name:
		# each string name in the tuple represents a required
		# CGI parameter
		if type(elt) == StringType:
		    try:
			if type(elt) == ListType:
			    v = []
			    for e in elt:
				v.append(e.value)
			    result.append(v)
			else:
			    result.append(self[elt].value)
		    except (AttributeError, KeyError):
			missing.append(elt)
		# each tuple in the tuple represents a CGI parameter,
		# at least one of which must be present
		elif type(elt) == TupleType:
		    r = None
		    for n in elt:
			# look for the first one
			try:
			    r = self[n].value
			except KeyError:
			    continue
			break
		    if r is None:
			missing.append(elt)
		    else:
			result.append(r)
	    if missing:
		raise ValidationError, tuple(missing)
	    else:
		return tuple(result)
	else:
	    raise TypeError, 'invalid name argument'

    def make_optional(self, name):
	if type(name) == StringType:
	    try:
		return self[name].value
	    except KeyError:
		return None
	elif type(name) == TupleType:
	    for elt in name:
		# Each string name in the tuple represents an optional
		# CGI parameter. Only the first found is returned.
		try:
		    return self[elt].value
		except KeyError:
		    pass
	    return None
	else:
	    raise TypeError, 'invalid name argument'

    def validate(self):
	"""Check inputs against stated required and optional inputs"""

	missing = []
	badcheck = []
	for name, checkfunc, params in self._required:
	    try:
		arg = self.make_required(name)
		if checkfunc is not None:
		    if params is not None:
			params = (self.param_map[name], arg) + params
		    else:
			params = (self.param_map[name], arg)
		    try:
			apply(checkfunc, params)
		    except ValidationError, msg:
			badcheck.append(msg)
	    except ValidationError, args:
		missing.append(args)

	for (name, checkfunc, params) in self._optional:
	    tup = self.make_optional(name)
	    if tup and checkfunc is not None:
		if params is not None:
		    params = (self.param_map[name], tup) + params
		else:
		    params = (self.param_map[name], tup)
		try:
		    apply(checkfunc, params)
		except ValidationError, msg:
		    badcheck.append(msg)

	if (missing or badcheck) and self.log_errors:
	    self.log_error(missing, badcheck)

	if (missing or badcheck) and self.generate_error_page:
	    self.generate_HTML(missing, badcheck)

	self.missing = missing
	self.badcheck = badcheck

	return not (missing or badcheck)

    def map_missing(self, missing):
	output = []
	for m in missing:
	    if type(m) == StringType:
		output.append('<li> %s\n' % self.param_map[m])
	    elif type(m) == TupleType:
		m2 = []
		for e_and in m:
		    if type(e_and) == StringType:
			m2.append(self.param_map[e_and])
		    else:
			_tmp = []
			for e_or in e_and:
			    _tmp.append(self.param_map[e_or])
			_tmp = string.join(_tmp, ' or ')
			m2.append('(%s)' % _tmp)
		output.append('<li> %s\n' % string.join(m2, ' and '))
	return string.join(output, "")

    def generate_HTML(self, missing, badcheck):
	_emit('Content-type: text/html\n\n'
	      '<html>\n'
	      '<head><title>CGI Error</title></head>\n'
	      '<body>\n\n'
	      '<h1>CGI Error</h1>\n\n')

	if missing:
	    _emit('<p>The following required parameters were not given:\n'
		  '<ul>\n')
	    _emit(self.map_missing(missing))
	    _emit('</ul>\n')

	if badcheck:
	    _emit('<p>The following type check errors were discovered:\n'
		  '<ul>\n')
	    for b in badcheck:
		_emit('<li> %s\n' % b)
	    _emit('</ul>\n')

	_emit('</body>\n')
	_emit('</html>\n')

    def log_error(self, missing, badcheck):
	if missing:
	    sys.stderr.write('CGI Error, missing parameters: %s\n' % `missing`)
	if badcheck:
	    for b in badcheck:
		sys.stderr.write('CGI Error, check error: %s\n' % b)

class HiddenMixin:

    def _parse_arg(self, v):
	if v == 'None':
	    return None
	try:
	    v = string.atoi(v)
	except ValueError:
	    try:
		v = string.atof(v)
	    except ValueError:
		pass
	return v

    def _parse_type(self, typ, val):
	type_info = string.split(typ, ":")
	nlen = len(type_info)
	if type_info[0] == 'req':
	    add = self.add_required
	elif type_info[0] == 'opt':
	    add = self.add_optional

	names = string.split(val, ',')
	if nlen == 1:
	    map(add, names)
	else:
	    try:
		checkfunc = eval('check%s'%type_info[1])
	    except NameError:
		# check function missing - what to do?
		return
	    if nlen == 2:
		map(add, names, len(names)*[checkfunc])
	    else:
		args = tuple(map(self._parse_arg, type_info[2:]))
		map(add, names, len(names)*[checkfunc], len(names)*[args])

class HiddenFieldStorage(HiddenMixin, ValidatedFieldStorage):
    '''ValidatedFieldStorage subclass that gets type info from the form itself.

    This is not secure, since anyone on the net can write a form and subvert
    the intentions of the script author.  Nevertheless, it is useful for non-
    critical applications, as the form author can specify everything in the
    form itself.

    Required and optional parameters are specified using hidden parameters
    of the form:

        <input type=hidden name="(req|opt)[:typ[:min[:max]]]"
		value="p1[,p2][,p3] ...">

    req can be either "req" or "opt".  typ can be the suffix of any function
    beginning with "check", such as "checkint", "checkdate" or "checkfloat".
    Optional min and max parameters can be given where the check functions
    accept them.  (None can be specified to indicate an unspecified min or
    max.)  The value if the field is a comma-separated list of parameters
    which are to assume the properties given in the name.

    A short example:

        <input type=hidden name="req:int:1:None" value=v1>
        <input type=hidden name="req:float:None:50.5" value=v2>
        <input type=hidden name="req" value=v3>
	<input type=hidden name="opt:int:1:4" value=v4>

    Note that this class is not as flexible as its superclass,
    ValidatedFieldStorage.  it cannot be used to validate groups of
    parameters, nor can the form author specify a mapping from variable
    names to friendlier human usage.

    '''

    def __init__(self, fp=None, headers=None, outerboundary="",
		 environ=os.environ, keep_blank_values=None,
		 generate_error_page=1, log_errors=0):
	ValidatedFieldStorage.__init__(self, fp, headers, outerboundary,
				       environ, keep_blank_values,
				       generate_error_page, log_errors)

	for key in self.keys():
	    if key[0:3] not in ['opt', 'req']:
		continue
	    self._parse_type(key, self[key].value)

class HiddenFileFieldStorage(HiddenMixin, ValidatedFieldStorage):
    '''ValidatedFieldStorage that gets type info from a file on the server.

    This is similar to HiddenFieldStorage, except only a pointer to a file
    containing parameter type information resides in the form itself.  This
    is perhaps more secure, presuming access to the file system on the server
    is not compromised.

    A single hidden parameter is used to name a file that holds parameter
    type information.  That file is parsed for type information.

    A short example:
	
        <input type=hidden name="type_file" value="/home/dolphin/skip/types.dat">

    The format of lines in the file is
    
	typeinfo = paramlist

    e.g.:

	req:int:1:4 = v1,v2

    This class has the same deficiency that complex type checks are impossible
    to perform and the parameter names cannot be mapped to friendlier forms.
    For either of those capabilities, ValidatedFieldStorage is required.
    '''

    def __init__(self, fp=None, headers=None, outerboundary="",
		 environ=os.environ, keep_blank_values=None,
		 generate_error_page=1, log_errors=0):
	ValidatedFieldStorage.__init__(self, fp, headers, outerboundary,
				       environ, keep_blank_values,
				       generate_error_page, log_errors)

	try:
	    type_file = self['type_file'].value
	except KeyError:
	    # check file missing - what to do?
	    return

	try:
	    f = open(type_file)
	except IOError:
	    # can't open file - what to do?
	    return
	
	for line in map(string.strip, f.readlines()):
	    [typ, val] = map(string.strip, string.split(line, '='))
	    self._parse_type(typ, val)

### helper functions

def checkint(name, val, mn=None, mx=None):
    """Check that input is an integer - optional arguments denote bounds"""
    try:
	if val[0:2] == '0x' or val[0:2] == '0X':
	    x = string.atoi(val, 16)
	elif val[0:0] == '0':
	    x = string.atoi(val, 8)
	else:
	    # allow commas as long as they are properly spaced
	    x = string.split(val, ",")
	    if len(x) > 1:
		for e in x[1:]:
		    if len(e) != 3:
			raise ValidationError, \
			      '%s is not a valid integer' % val
		if len(x[0]) < 1 or len(x[0]) > 3:
		    raise ValidationError, \
			  '%s is not a valid integer' % val
		val = re.sub(",", "", val)
	    x = string.atoi(val)
	if ((mn is not None and x < mn) or
	    (mx is not None and x > mx)):
		raise ValidationError, \
		      'parameter "%s", value "%s" is out of range' % \
		      (name, val)
	return
    except ValueError:
	raise ValidationError, '%s is not a valid integer' % val

def checkfloat(name, val, mn=None, mx=None):
    """Check that input is a float - optional arguments denote bounds"""
    try:
	x = string.atof(val)
	if ((mn is not None and x < mn) or
	    (mx is not None and x > mx)):
		raise ValidationError, \
		      'parameter "%s", value "%s" is out of range' % \
		      (name, val)
	return
    except ValueError:
	raise ValidationError, '%s is not a valid floating point number' % val


# kind of simple-minded, but should catch a fair number of errors
# the checkdate function is in transition between using regex and using re,
# hence the extra complexity
try:
    import re
    _slash = re.compile('[ \t]*[0-9]+[-/]([a-z]+|[0-9]+)[-/][0-9]+[ \t]*$', re.I)
    _amer = re.compile('[ \t]*([a-z]+)[ \t]*([0-9]+),?[ \t]*([0-9]+)[ \t]*$', re.I)
    _euro = re.compile('[ \t]*([0-9]+)[ \t]*([a-z]+)[ \t]*([0-9]+)[ \t]*$', re.I)
except ImportError:
    import regex
    _slash = regex.compile('[ \t]*[0-9]+[-/]\([a-z]+\|0-9]+\)[-/][0-9]+[ \t]*$',
			   regex.casefold)
    _amer = regex.compile('[ \t]*\([a-z]+\)[ \t]*\([0-9]+\),?[ \t]*\([0-9]+\)[ \t]*$',
			  regex.casefold)
    _euro = regex.compile('[ \t]*\([0-9]+\)[ \t]*\([a-z]+\)[ \t]*\([0-9]+\)[ \t]*$',
			  regex.casefold)

def checkdate_regex(name, val):
    """Simple date validator for demonstration purposes"""
    mnames = calendar.month_name + calendar.month_abbr
    if _slash.match(val) != -1:
	if string.capitalize(_slash.group(1)) in mnames:
	    return
	try:
	    x = string.atoi(_slash.group(1))
	except ValueError:
	    raise ValidationError, 'parameter "%s", value "%s" does not look like a date' % \
		  (name, val)
    if _amer.match(val) != -1 and string.capitalize(_amer.group(1)) in mnames:
	return
    if _euro.match(val) != -1 and string.capitalize(_euro.group(2)) in mnames:
	return
    raise ValidationError, 'parameter "%s", value "%s" does not look like a date' % \
	  (name, val)

def checkdate_re(name, val):
    """Simple date validator for demonstration purposes"""
    mnames = calendar.month_name + calendar.month_abbr
    mat = _slash.match(val)
    if mat is not None:
	if string.capitalize(mat.group(1)) in mnames:
	    return
	try:
	    x = string.atoi(mat.group(1))
	except ValueError:
	    raise ValidationError, \
		  'parameter "%s", value "%s" does not look like a date' % \
		  (name, val)
    mat = _amer.match(val)
    if (mat is not None and
	string.capitalize(mat.group(1)) in mnames):
	return
    mat = _euro.match(val)
    if (mat is not None and
	string.capitalize(mat.group(2)) in mnames):
	return
    raise ValidationError, \
	  'parameter "%s", value "%s" does not look like a date' % \
	  (name, val)

try:
    x = re
    checkdate = checkdate_re
except NameError:
    checkdate = checkdate_regex

# only used for the test!
def _checkcity(name, val):
    if val[1] != 'CA':
	raise ValidationError, 'State must be CA'

def test1():
    print "Test 1",

    # four simple parameters
    os.environ['QUERY_STRING'] = ('v1=10'
				  '&v2=47.00'
				  '&v3=dog'
				  '&v4=5')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_required('v1', checkint, (1, None))
    form.add_required('v2', checkfloat, (None, 50.5))
    form.add_required('v3')
    form.add_optional('v4', checkint, (1,4))
    form.set_parameter_map({'v1': 'Quantity', 'v2': 'Unit Cost',
			    'v3': 'Description', 'v4': 'Other Info'})
    form.generate_error_page = 0
    if not form.validate(): print "passed"
    else: print "failed"

def test2():
    print "Test 2",

    # third case - one compound parameter with an invalid part - generate
    # an error page only
    os.environ['QUERY_STRING'] = ('city=Beverly+Hills'
				  '&state=FL'
				  '&zip=90210')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_required(('city', ('state', 'country'), 'zip'),
		      _checkcity)
    form.generate_error_page = 0
    if not form.validate(): print "passed"
    else: print "failed"

def test3():
    print "Test 3",

    # third case - one compound parameter
    os.environ['QUERY_STRING'] = ('city=Beverly+Hills'
				  '&zip=90210'
				  '&date=31/Mar/97')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_required(('city', ('state', 'country'), 'zip'),
		      _checkcity)
    form.add_optional('date', checkdate)
    form.generate_error_page = 0
    if not form.validate(): print "passed"
    else: print "failed"

def test4():
    print "Test 4",

    # fourth case - a couple dates - both optional - no error logging or HTML
    # generation, just return an error indication.
    os.environ['QUERY_STRING'] = ('start=31/Mar/97'
				  '&end=April 4, 1997')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_optional('start', checkdate)
    form.add_optional('end', checkdate)
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test5():
    print "Test 5",

    # a couple dates - both optional - no error logging or HTML
    # generation, just return an error indication.
    os.environ['QUERY_STRING'] = ('start=31/March/97'
				  '&end=5 May 1997')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_optional('start', checkdate)
    form.add_optional('end', checkdate)
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test6():
    print "Test 6",

    # same as test 5 but using hidden fields to specify type info
    os.environ['QUERY_STRING'] = ('start=31/March/97'
				  '&end=5 May 1997'
				  '&opt:date=start,end')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = HiddenFieldStorage()
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test7():
    print "Test 7",

    # like test 4 but using HiddenFieldStorage
    os.environ['QUERY_STRING'] = ('start=31/Mar/97'
				  '&end=April 4, 1997'
				  '&opt:date=start,end')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = HiddenFieldStorage()
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test8():
    print "Test 8",

    # like test1 but with HiddenFieldStorage
    os.environ['QUERY_STRING'] = ('v1=10'
				  '&v2=47.00'
				  '&v3=dog'
				  '&v4=5'
				  '&req:int:1=v1'
				  '&req:float:None:50.5=v2'
				  '&req=v3'
				  '&opt:int:1:4=v4')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = HiddenFieldStorage()
    form.generate_error_page = 0
    form.validate()
    if not form.validate(): print "passed"
    else: print "failed"

def test9():
    print "Test 9",

    # like test8 but with HiddenFileFieldStorage
    f = open('/tmp/parms.txt', 'w')
    f.write('req:int:1 = v1\nreq:float:None:50.5=v2\nreq = v3\nopt:int:1:4=v4\n')
    f.close()
    os.environ['QUERY_STRING'] = ('v1=10'
				  '&v2=47.00'
				  '&v3=dog'
				  '&v4=5'
				  '&type_file=/tmp/parms.txt')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = HiddenFileFieldStorage()
    form.generate_error_page = 0
    if not form.validate(): print "passed"
    else: print "failed"
    os.unlink('/tmp/parms.txt')

def test10():
    print "Test 10",

    # simple test - multi-valued parameter
    os.environ['QUERY_STRING'] = ('keywords=folk'
				  '&keywords=acoustic')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_required('keywords')
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test11():
    print "Test 11",

    # simple test - multi-valued parameter
    os.environ['QUERY_STRING'] = ('keywords=folk'
				  '&keywords=acoustic'
				  '&city=Scotia'
				  '&state=NY')
    os.environ['REQUEST_METHOD'] = 'GET'
    form = ValidatedFieldStorage()
    form.add_required('keywords')
    form.add_required(('city', 'state'))
    form.generate_error_page = 0
    if form.validate(): print "passed"
    else: print "failed"

def test():
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    test8()
    test9()
    test10()
    test11()

if __name__ == '__main__':
    test()
