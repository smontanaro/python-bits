#!/usr/bin/env python

import getopt
import quopri
import base64
import sys

#               QP?    Decode?
codingfuncs = {(True,  True): quopri.decode,
               (True,  False): lambda x,y: quopri.encode(x,y,False),
               (False, True): base64.decode,
               (False, False): base64.encode}

qp = False
decode = False
opts, args = getopt.getopt(sys.argv[1:], "qu")
for opt, arg in opts:
    if opt == "-q":
        qp = True
    elif opt == "-u":
        decode = True

codingfuncs[(qp, decode)](sys.stdin, sys.stdout)

    
