#!/usr/bin/python

import time
import sys
import plc

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

    type = None
    if 'type' in d:
        type = d['type']
    else:
        print "No type specified (--type <type>)"
        sys.exit(1)

    if 'H' in d:
        hostname = d['H']
    else:
        print "No hostname specified (-H <hostname>)"
        sys.exit(1)

    # TODO: have two thresholds.  One for warning, another for critical.

    print "No cycles detected for %s" % hostname
    sys.exit(0)

        
if __name__ == '__main__':
    main()
