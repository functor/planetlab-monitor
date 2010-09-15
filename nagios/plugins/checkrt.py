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

def get_next_pattern(argv, last):
    """ This is worse than the function above. """
    i = 0
    if last is not None:
        for a in argv:
            if argv[i] == last:
                break
            i += 1
    for offset,a in enumerate(argv[i+1:]):
        if a == "-p":
            return argv[i+2+offset]
    return None


def main():
    #d = argv_to_dict(sys.argv[1:])
    r = -1
    o = -1
    last = None

    while True:
        pattern = get_next_pattern(sys.argv, last)
        if pattern == None:
            break
        last = pattern

        (r_ret,o_ret) = look_for_pattern(pattern)
        r = max(r, r_ret)
        o = max(o, o_ret)

    if r == 3:
        print "UNKNOWN: failed to convert %s to open ticket count" % o
        sys.exit(3)
    elif r == 0:
        print "OK: no open tickets for site"
        sys.exit(0)
    elif r == 1:
        print "WARNING: %s open tickets" % o
        sys.exit(1)
    else:
        print "FAKE-CRITICAL: RT check failed"
        sys.exit(2)

def look_for_pattern(pattern):

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

   # print >>sys.stderr, cmd
   # print >>sys.stderr, os.environ
    out = os.popen(cmd, 'r')
    open_tickets = out.read()

    try:
        open_tickets_i = int(open_tickets)
    except:
        return (3,None)

    if open_tickets_i == 0:
        return (0,0)
    elif open_tickets_i != 0:
        return (1,open_tickets_i)
    else:
        return (2,open_tickets_i)


if __name__ == '__main__':
    f = open("/tmp/checkrt", 'a')
    f.write("checkrt %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
    f.close()
    main()
