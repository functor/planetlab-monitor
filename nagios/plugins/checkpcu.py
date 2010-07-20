#!/usr/bin/python

import time
import sys
import os

from monitor.wrapper import plc

def argv_to_dict(argv):
    """
        NOTE: very bare-bones, no error checking, will fail easily.
    """
    d = {}
    prev=None
    for a in argv:
        if "--" == a[0:2]:
            prev = a[2:]
        elif "-" == a[0:1]:
            prev = a[1:]
        else:
            d[prev] = a
    return d

def main():
    d = argv_to_dict(sys.argv[1:])

    api = plc.api
    if 'hostname' in d or 'H' in d:
        try:
            hostname = d['host']
        except:
            hostname = d['H']
    else:
        print "UNKNOWN: Argument error"
        sys.exit(3)

    try:
        n = api.RebootNodeWithPCU(hostname, True)
    except Exception, e:
        if "No PCUs associated with Node" in str(e):
            print "CRITICAL: Failure: %s" % str(e)
            sys.exit(2)
        else:
            print "UNKNOWN: Failure: %s" % str(e)
            sys.exit(3)

    t1 = 0
    t2 = time.time()

    try:
        pcu_id = api.GetNodes(hostname)[0]['pcu_ids'][0]
        pcu = api.GetPCUs({'pcu_id' : pcu_id})[0]
    except Exception, e:
        print "UNKNOWN: API Error: %s" % str(e)
        sys.exit(3)

    if n == 0:
        print "%s: PCU test successful" % pcu['model']
        sys.exit(0)
    elif n != 0:
        print "%s: PCU test failure: %s" % (pcu['model'], n)
        sys.exit(1)
    else:
        print "FAKE-CRITICAL: PCU test failed"
        sys.exit(2)


if __name__ == '__main__':
    f = open("/tmp/checkpcu", 'a')
    f.write("checkpcu %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
    f.close()
    main()
