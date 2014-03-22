
'''

generate a dictionary that maps the extensions in the mime.types
file into appropriate MIME types.

'''

# this should be discovered - how?
type_file = '/usr/local/etc/httpd/conf/mime.types'

types = {}

def init_types():
    import string
    for line in map(string.strip, open(type_file).readlines()):
	if not line or line[0] == '#': continue
	fields = string.split(line)
	if len(fields) < 2: continue
	for ext in fields[1:]:
	    types[ext] = string.lower(fields[0])
	
def get_type(path):
    import string
    if not types: init_types()
    ext = string.lower(string.split(path, '.')[-1])
    if types.has_key(ext):
	fmimetype = types[ext]
    else:
	fmimetype = 'text/plain'
    return fmimetype

