#!/usr/local/bin/python

import httplib, sys, string, regsub

def massage(stuff):
    stuff = regsub.gsub('\(GRAND PRAIRIE\|CALGARY\|EDMONTON\|MEDICINE HAT\) *, *CA', '\\1, AB', stuff)    
    stuff = regsub.gsub('\(WHISTLER\|VANCOUVER\) *, *CA', '\\1, BC', stuff)
    stuff = regsub.gsub('WINNIPEG *, *CA', 'WINNIPEG, MB', stuff)
    stuff = regsub.gsub('\(GRAND FALLS\) *, *CA', '\\1, NF', stuff)
    stuff = regsub.gsub('CANSO *, *CA', 'CANSO, NS', stuff)
    stuff = regsub.gsub('\(EMO\|TORONTO\|OTTAWA\|HAMILTON\|GUELPH LAKE'
			'\|BARRIE\|EAST KITCHENER\|BARRIE'
			'\) *, *CA', '\\1, ON', stuff)
    stuff = regsub.gsub('QUEBEC CITY', 'QUEBEC', stuff)
    stuff = regsub.gsub('\(ALMA\|BUCKINGHAM\|MONTREAL\|QUEBEC\) *, *CA', '\\1, QC', stuff)
    stuff = regsub.gsub('SASKATOON *, *CA', 'SASKATOON, SK', stuff)
    stuff = regsub.gsub('<td>\([^,]*\),[^<]*</td> </tr>$',
			'<td>\\1</td> </tr>', stuff)
    stuff = regsub.gsub(', *AUST?\., *AU<', ', AU<', stuff)
    stuff = regsub.gsub('; *AU<', ', AU<', stuff)
    stuff = regsub.gsub("\(<TD><FONT SIZE=2><A HREF=/musicdb/\?MIval=tourquery_v&venue=[0-9]+>\)\([^,<]*\),[^<]*\(.*\)", "\\1\\2\\3", stuff)
    return stuff

def main():
    input = string.strip(sys.stdin.readline())

    if input:
	query_string = 'MIval=tourquery_a&days=90&artist=%s' % input

	httpobj = httplib.HTTP('www.automatrix.com', 3128)
	httpobj.putrequest('POST', 'http://www2.music.sony.com/musicdb/')
	httpobj.putheader('Host', 'www2.music.sony.com')
	httpobj.putheader('Connection', 'Keep-Alive')
	httpobj.putheader('Accept', 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*')
	httpobj.putheader('Content-type', 'application/x-www-form-urlencoded')
	httpobj.putheader('Content-length', '%d' % len(query_string))
	httpobj.endheaders()
	httpobj.send(query_string)

	reply, msg, hdrs = httpobj.getreply()
	stuff = massage(httpobj.getfile().read())
	sys.stdout.write(stuff)
