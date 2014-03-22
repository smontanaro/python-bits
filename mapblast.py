#!/usr/bin/env python

import httplib, re, string, sys, time

# modify to suit your environment
proxyhost = "orca.automatrix.com"
proxyport = 3128

# the following state info was pulled from another module I wrote so
# you wouldn't have to include my entire environment...
#--------------------------------------------------------------------------
# map state names to abbreviations
states = {'Alabama':'AL', 'Alaska':'AK', 'Arizona':'AZ', 'Arkansas':'AR',
	  'California':'CA', 'Oregon':'OR', 'Washington':'WA', 'Idaho':'ID',
	  'Montana':'MT', 'Wyoming':'WY', 'Utah':'UT', 'Colorado':'CO',
	  'New Mexico':'NM', 'North Dakota':'ND', 'South Dakota':'SD',
	  'Nebraska':'NE', 'Kansas':'KS', 'Oklahoma':'OK', 'Texas':'TX',
	  'Minnesota':'MN', 'Iowa':'IA', 'Missouri':'MO', 'Louisiana':'LA',
	  'Wisconsin':'WI', 'Illinois':'IL', 'Kentucky':'KY', 'Tennessee':'TN',
	  'Mississippi':'MS', 'Michigan':'MI', 'Indiana':'IN', 'Ohio':'OH',
	  'West Virginia':'WV', 'Virginia':'VA', 'North Carolina':'NC',
	  'Georgia':'GA', 'Florida':'FL', 'Maryland':'MD', 'DC':'DC',
	  'District of Columbia':'DC', 'Delaware':'DE', 'New Jersey':'NJ',
	  'Pennsylvania':'PA', 'New York':'NY', 'Vermont':'VT', 'Maine':'ME',
	  'New Hampshire':'NH', 'Massachusetts':'MA', 'Connecticut':'CT',
	  'Rhode Island':'RI', 'Guam':'GU', 'Puerto Rico':'PR',
	  'Virgin Islands':'VI', 'Alberta':'AB',
	  'British Columbia':'BC', 'Manitoba':'MB', 'Newfoundland':'NF',
	  'Nova Scotia':'NS', 'Ontario':'ON', 'Prince Edward Island':'PE',
	  'Quebec':'QC', 'Saskatchewan':'SK', 'Northwest Territories':'NT',
	  'Yukon':'YT', 'New Brunswick':'NB', 'Nevada': 'NV',
	  'South Carolina':'SC', "Hawai'i":'HI', 'Hawaii':'HI',
	  'PEI':'PE', 'District Of Columbia':'DC', 'PQ':'QC', 'QUE':'QC',
	  'QU':'QC', 'ONT':'ON', 'ALB':'AB', 'MAN':'MB', 'SAS':'SK',
	  'American Samoa':'AS',
	  'Marshall Islands':'MH', 'Federated States of Micronesia':'FM',
	  'Palau':'PW', 'Northern Mariana Islands':'MP'}

# reverse mapping
state_abbrevs = {}
for i in states.keys(): state_abbrevs[states[i]] = i
state_abbrevs['HI'] = "Hawaii"
state_abbrevs['DC'] = 'District of Columbia'
state_abbrevs['QC'] = 'Quebec'
state_abbrevs['ON'] = 'Ontario'
state_abbrevs['AB'] = 'Alberta'
state_abbrevs['PE'] = 'Prince Edward Island'
state_abbrevs['SK'] = 'Saskatchewan'
state_abbrevs['MB'] = 'Manitoba'

# other common abbreviations
state_abbrevs['MASS'] = 'Massachusetts'
state_abbrevs['MICH'] = 'Michigan'
state_abbrevs['CALIF'] = 'California'
state_abbrevs['WIS'] = 'Wisconsin'
state_abbrevs['WISC'] = 'Wisconsin'
state_abbrevs['TENN'] = 'Tennessee'
state_abbrevs['ORE'] = 'Oregon'
state_abbrevs['ILL'] = 'Illinois'
state_abbrevs['WVA'] = 'West Virginia'

# clump the states and provinces into regions
west = ['ID', 'HI', 'AK', 'WA', 'CA', 'UT', 'NV', 'OR', 'AZ', 'AS', 'MH',
	'PW', 'MP', 'FM', 'GU']
middle = ['MT', 'WY', 'CO', 'NM', 'ND', 'SD', 'NE', 'KS',
	  'OK', 'TX', 'MN', 'IA', 'MO', 'AR', 'LA']
east = ['WI', 'IL', 'MI', 'IN', 'KY', 'TN', 'MS', 'AL', 'GA', 'FL', 'SC',
	'NC', 'VA', 'OH', 'WV', 'PA', 'DC', 'MD', 'DE', 'NJ', 'NY', 'CT',
	'RI', 'MA', 'VT', 'NH', 'ME', 'VI', 'PR']
us = west + middle + east
canada = ['AB', 'BC', 'MB', 'NF', 'NS', 'ON', 'PE', 'QC', 'SK', 'NT',
	  'YT', 'NB']
#--------------------------------------------------------------------------

def lookup(city, state):

    state = string.capwords(state)
    st = string.upper(state)
    if states.has_key(state):
	st = states[state]
    elif state_abbrevs.has_key(st):
	pass
    else:
	print "oops!"			# this is just a demo, after all!
	raise ValueError

    if st in canada:
	country = "CAN"
    else:
	country = "USA"

    qs = ("FAM=mapblast&CMD=GEO&SEC=blast&"
	  "AD3=%(city)s,%(st)s&AD4=%(country)s" %  locals())
    qs = re.sub(" ", "+", qs)

    # this proxy server should work...
    h = httplib.HTTP(proxyhost, proxyport)
    h.putrequest('GET', 'http://www.mapblast.com/yt.hm?%s' % qs)
    h.putheader('Host', 'www.mapblast.com')
    h.putheader('Accept-Language', 'en')
    h.putheader('Accept-Charset', 'iso-8859-1,*,utf-8')
    h.putheader('Accept', 'text/html')
    h.putheader('Content-type', 'application/x-www-form-urlencoded')
    h.endheaders()

    errcode, errmsg, headers = h.getreply()
    if errcode != 200:
	raise TypeError

    time.sleep(0.3)
    output = h.getfile().read()

    llpat = re.compile("LT:([^|]+)\|"	# lat
		       "LN:([^|]+)\|"	# long
		       "LS:(?:[^|]+)\|"	# ??
		       "c:([^|]+)\|"	# city
		       "s:([^|]+)\|",	# state
		       re.I)
    match = llpat.search(output)
    if match is not None:
	lat, long, city, st = match.groups()
    else:
	lat = long = "?"
    
    city = re.sub("_", " ", city)

    return string.lower("%s:%s::%s:%s" % (city, st, lat, long))

if __name__ == "__main__":
    (city, state) = (sys.argv[1], sys.argv[2])
    print lookup(city, state)

