#!/usr/bin/python

import sys
import os

def recent(q, val, length):
    return [val] + q[:length-1]

def add(d, path, v):
    if path not in d:
        d[path] = []
    d[path] = recent(d[path], v, 6)
    #d[path].append(v)

def stateof(l):
    if len(set(l)) == 1:
        return l[0]
    else:
        return "BOOT"

def in_hard_state(l):
    if len(set(l)) == 1:
        return True
    else:
        return False

def main():
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.set_defaults(database="",
                        sheet="",
                        fields="date_checked,timestamp_unix,hostname,uptime,kernel_version,observed_status",
                        values=None,
                        valuelist=None,
                        update=None,
                        fieldpositions=None,
                        showfieldpositions=False,
                        create=False)
    parser.add_option("", "--database", dest="database", help="")
    parser.add_option("", "--create", dest="create", action="store_true", help="")
    parser.add_option("", "--sheet",  dest="sheet", help="")
    parser.add_option("", "--values", dest="values", help="")
    parser.add_option("", "--valuelist", dest="valuelist", help="")
    parser.add_option("", "--update", dest="update", help="")
    parser.add_option("", "--fields", dest="fields", help="")
    parser.add_option("", "--fieldpositions", dest="fieldpositions", help="")
    parser.add_option("", "--showfieldpositions", dest="showfieldpositions", action="store_true", help="")
    (config, args) = parser.parse_args()

    if config.fields:
        config.fields = config.fields.split(',')

    if config.fieldpositions:
        config.fieldpositions = [ int(x) for x in config.fieldpositions.split(',') ]

    first = True
    #for f in config.fields:
    #    print "%s,"%f,
    #print ""

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        # NOTE assumes ts are ordered.
        #try:
        if True:
            fields = line.split(',')
            if first:
                headers = [ f for f in fields ]
                #for i,f in enumerate(headers):
                #    print i, headers[i]
                first=False
                if config.showfieldpositions:
                    for f in config.fields:
                        i = headers.index(f)
                        print i,
                    print ""


        #except:
        #    print >>sys.stderr, "EXCEPTION:", line
        #    sys.exit(1)
        #for i,f in enumerate(fields):
            #print i, headers
            #print i, f
        #    print i, headers[i], f

        for pos,f in enumerate(config.fields):

            if config.fieldpositions:
                i = config.fieldpositions[pos]
            else:
                try:
                    i = headers.index(f)
                except:
                    print "could not find field: %s" % f
                    sys.exit(1)

            try:
                v = fields[i]
            except:
                continue
            
            print "%s," % v,
        print ""

if __name__ == "__main__":
    main()
