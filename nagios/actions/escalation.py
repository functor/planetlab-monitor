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

def main(f):
    d = argv_to_dict(sys.argv[1:])

    site = None
    if 'site' in d:
        site = d['site'].replace('site-cluster-for-','')
    else:
        print "No site specified"
        sys.exit(1)
        
    notificationnumber = 1
    if 'notificationnumber' in d or 'n' in d:
        try:
            notificationnumber = int(d['notificationnumber'])
        except:
            notificationnumber = int(d['n'])

    interval = 1
    if 'interval' in d:
        interval = int(d['interval'])

    type = None
    if 'notificationtype' in d:
        type = d['notificationtype']

    if type == "RECOVERY":
        f.write("\t   %s %s\n" % (time.time(), "enableSiteSliceCreation(%s)" % site ))
        f.write("\t   %s %s\n" % (time.time(), "enableSiteSlices(%s)" % site ))
        #plc.enableSiteSliceCreation(site)
        #plc.enableSiteSlices(site)

    elif type == "PROBLEM":
        if notificationnumber <= 3:
            pass
        elif notificationnumber <= 6:
            f.write("\t   %s %s\n" % (time.time(), "removeSiteSliceCreation(%s)" % site ))
            #plc.removeSiteSliceCreation(site)
        elif notificationnumber > 6:
            f.write("\t   %s %s\n" % (time.time(), "removeSiteSliceCreation(%s)" % site ))
            f.write("\t   %s %s\n" % (time.time(), "suspendSiteSlices(%s)" % site ))
            #plc.removeSiteSliceCreation(site)
            #plc.suspendSiteSlices(site)

if __name__ == '__main__':
    f = open("/tmp/escalation", 'a')
    f.write("escalation %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
    main(f)
    f.close()
