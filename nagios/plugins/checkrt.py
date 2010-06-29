#!/usr/bin/python

import os
import time
import sys
import auth

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

    if 'pattern' in d or 'p' in d:
        try:
            pattern = d['pattern']
        except:
            pattern = d['p']
    else:
        print "UNKNOWN: Argument error"
        sys.exit(3)


    # TODO: check that RT is configured correctly
    os.environ["RTSERVER"] = auth.RTSERVER
    os.environ["RTUSER"] = auth.RTUSER
    os.environ["RTPASSWD"] = auth.RTPASSWD
    os.environ["RTDEBUG"] = auth.RTDEBUG

    # TODO: may need to add a timeout
    # NOTE: RT3.8
    query = "Subject like '%%%s%%' and Queue='Monitor' and ( Status='new' or Status='open' )" % pattern
    cmd = """rt ls -s -t ticket "%s" 2>&1 """ % query
    cmd = cmd + """| grep -vi "no match" | wc -l """

    out = os.popen(cmd, 'r')
    open_tickets = out.read()

    try:
        open_tickets_i = int(open_tickets)
    except:
        print "UNKNOWN: failed to convert %s to open ticket count" % open_tickets
        sys.exit(3)

    if open_tickets_i == 0:
        print "OK: no open tickets for site"
        sys.exit(0)
    elif open_tickets_i != 0:
        print "WARNING: %s open tickets" % open_tickets_i
        sys.exit(1)
    else:
        print "FAKE-CRITICAL: RT check failed"
        sys.exit(2)


if __name__ == '__main__':
    f = open("/tmp/checkpcu", 'a')
    f.write("checkpcu %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
    f.close()
    main()
