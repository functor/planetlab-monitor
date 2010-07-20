#!/usr/bin/python

from optparse import OptionParser

import plc
import auth
import sys
import time

parser = OptionParser()
parser.add_option("-H", "--hostname", dest="hostname", help="Check API at given hostname.")
parser.add_option("-s", "--seconds", dest="seconds", type="int", default=60, help="Number of seconds for a slow reply.")
(options, args) = parser.parse_args()

server = "https://" + options.hostname + "/PLCAPI/"
api = plc.PLC(auth.auth, server)

try:
    t1 = time.time()
    for f in ['GetNodes', 'GetSites', 'GetSlices']:
        m = api.__getattr__(f)
        n = m({'peer_id' : None, '-LIMIT' : 25})
        if len(n) < 10:
            print "CRITICAL: Failure: API returned too few responses"
            sys.exit(2)
    t2 = time.time()

    if t2-t1 > options.seconds:
        print "WARNING: API returned responses in less than %s seconds" % options.seconds
        sys.exit(1)
            
    print "API test successful"
    sys.exit(0)
except Exception, e:
    print "CRITICAL: Failure: %s" % str(e)
    sys.exit(2)
