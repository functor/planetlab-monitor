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

    site = None
    if 'site' in d:
        site = d['site'].replace('site-cluster-for-','')
    else:
        print "No site specified"
        sys.exit(1)

    # define escalation by observed properties about the site.
    # i.e. EXEMPT, level 0 (site enabled and slices ok), level 1 (site disabled), level 2 (slices)
    if plc.isSiteExempt(site):
        tags = plc.api.GetSiteTags({'login_base' : site, 'tagname' : 'exempt_site_until'})
        print "Exempt: %s is exempt until %s" % (site, tags[0]['value'])
        sys.exit(0)

    extra_str = ""
    
    # are slices disabled?
    slices_enabled = plc.areSlicesEnabled(site)
    if isinstance(slices_enabled, bool) and not slices_enabled:
        print "Level >= 2: slices are disabled at %s" % (site)
        sys.exit(0)
    elif isinstance(slices_enabled, type(None)):
        extra_str = "And, no slices."

    # Site is not exempt, so is it disabled?
    if not plc.isSiteEnabled(site):
        print "Level >= 1: site is disabled at %s. %s" % (site, extra_str)
        sys.exit(0)

    print "Level 0: no policy applied to site %s" % (site)
    sys.exit(0)

        
if __name__ == '__main__':
    main()
