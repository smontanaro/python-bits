#!/usr/bin/env python

'''
Netscreen-to-CSV converter...

Netscreen-formatted stuff is read on stdin, CSV stuff is written on stdout.

Netscreen syslog entry looks like this (wrapped for readability):

    Dec  2 12:34:50 2020rdg-idf-hsrp-663.northwestern.edu 2020rdg-idf-fw-1:
    NetScreen device_id=2020rdg-idf-fw-1  system-notification-00257(traffic):
    start_time="2003-12-02 12:34:47" duration=2 policy_id=4 service=icmp
    proto=1 src zone=trust-663 dst zone=Untrust action=Permit sent=1522
    rcvd=1518 src=129.105.213.125 dst=129.105.214.51 icmp type=8

We are interested in the device id and the stuff which begins with
"start_time=...".  Note that the column names for several multi-word keys
have spaces replaced by an underscore (e.g., "icmp_type" vs. "icmp type").
'''

import csv
import re
import sys
import socket
import getopt

class dialect(csv.excel):
    quoting=csv.QUOTE_NONNUMERIC

def get_services(f="/etc/services", services={}):
    if not services:
        for line in file(f):
            line = re.sub("#.*", "", line).strip()
            if not line:
                continue
            fields = line.split()
            name = fields[0]
            port_proto = fields[1]
            aliases = fields[2:]

            # convert port info into same format Netscreen uses
            port, proto = port_proto.split("/")
            port_proto = "%s/port:%s" % (proto, port)

            services[port_proto] = name
    return services

def get_name(ip, verbose=False, addresses={}):
    name = addresses.get(ip)
    if name is None:
        try:
            name = socket.gethostbyaddr(ip)[0]
            if verbose:
                name = "%s (%s)" % (name, ip)
        except socket.herror:
            name = ip
        addresses[ip] = name
    return name

def main(args):
    opts, args = getopt.getopt(args, "rv")
    resolve = False
    verbose = False
    for opt, arg in opts:
        if opt == "-r":
            resolve = True
        elif opt == "-v":
            verbose = True

    writer = csv.writer(sys.stdout, dialect=dialect)
    writer.writerow(('device_id', 'start_time', 'duration', 'policy_id',
                     'service', 'proto', 'src_zone', 'dst_zone', 'action',
                     'sent', 'rcvd', 'src', 'dst', 'src_port', 'dst_port'))

    pat1 = re.compile(r'NetScreen device_id=(\S+) .* start_time="([^"]+)"'
                      r' duration=(\S+) policy_id=(\S+) service=(\S+)'
                      r' proto=(\S+) src zone=(\S+) dst zone=(\S+)'
                      r' action=(\S+) sent=(\S+) rcvd=(\S+) src=(\S+)'
                      r' dst=(\S+) src_port=(\S+) dst_port=(\S+)')
    pat2 = re.compile(r'NetScreen device_id=(\S+) .* start_time="([^"]+)"'
                      r' duration=(\S+) policy_id=(\S+) service=(\S+)'
                      r' proto=(\S+) src zone=(\S+) dst zone=(\S+)'
                      r' action=(\S+) sent=(\S+) rcvd=(\S+) src=(\S+)'
                      r' dst=(\S+)')

    services = get_services()
    for line in sys.stdin:
        # try more complete row first
        mat = pat1.search(line)
        if mat is None:
            mat = pat2.search(line)

        if mat is None:
            continue
        
        groups = list(mat.groups())
        groups[4] = services.get(groups[4], groups[4])
        if resolve:
            groups[11] = get_name(groups[11], verbose)
            groups[12] = get_name(groups[12], verbose)
        try:
            writer.writerow(groups)
        except IOError:
            # output closed
            return

if __name__ == "__main__":
    main(sys.argv[1:])
