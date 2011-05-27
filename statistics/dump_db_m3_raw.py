#!/usr/bin/python

from monitor.database.info.model import *
import sys
from math import *
from monitor.generic import *
from datetime import datetime, timedelta
import time
import string

def list_to_str(list):
    ret = []
    for l in list:
        if type(l) == type([]):
            ret.append(" ".join([str(i) for i in l]))
        else:
            s = str(l)
            s = s.translate(string.maketrans(",\n\r\"", ";||'"))
            ret.append(s)
    return ret

def add_if_not_present(d, add_fields=None):
    if type(d) == type({}):
        key_list = d.keys()
        for k in add_fields.keys():
            if k not in key_list:
                d[k] = add_fields[k]
            else:
                add_if_not_present(d[k], add_fields[k])
    return

def dict_to_list(d, add_fields=None, ignore_fields=None):
    """ return a list of header names from a nested dict 
        { 'a' : 1, 'b' : { 'c':2, 'd' : 3}} 
        would return:
        [ 'a', 'b_c', 'b_d' ]
    """
    k_list = []
    d_list = []
    if add_fields: add_if_not_present(d, add_fields)
    for k in d.keys():
        if type(d[k]) == type({}):
            (z_kl, z_dl) = dict_to_list(d[k])
            for i,zk in enumerate(map(lambda x: "%s_%s" % (k,x), z_kl)):
                if ignore_fields is None or zk not in ignore_fields:
                    k_list.append(zk) 
                    d_list.append(z_dl[i]) 
        else:
            if ignore_fields is None or k not in ignore_fields:
                k_list.append(k)
                d_list.append(d[k])
    r = zip(k_list, list_to_str(d_list))
    r.sort(lambda x,y: cmp(x[0], y[0]))
    return ([ i[0] for i in r ], [ i[1] for i in r ])


if len(sys.argv) > 1 and sys.argv[1] == "--action":
    args = sys.argv[2:]
    find_action = True
else:
    if len(sys.argv) > 1:
        since_time = Time.str_to_dt(sys.argv[1], "%Y-%m-%d")
        skip = int(sys.argv[2])
        args = sys.argv[3:]
    else:
        args = sys.argv[1:]

    find_action = False

first_time = True
index = 0
t1=t2=0
if find_action:
    a = ActionRecord.query.all()
    print >>sys.stderr, len(a)
    for node in a:

        print >>sys.stderr, index, node.hostname, t2-t1
        index += 1
        t1 = time.time()

        d = node.__dict__
        (k,l) = dict_to_list(d)
        if first_time:
            print "timestamp_unix,%s" % ",".join(k[1:])
            first_time = False

        print "%s,%s" % (Time.dt_to_ts(d['date_created']), ",".join(l[1:]))
        t2=time.time()

else:
    ignore_fields = ['plc_node_stats_nodenetwork_ids', 'port_status_806', 'port_status_22', 'port_status_80' ]
    add_fields = {'plc_node_stats' : { 'last_boot' : 0, 'last_pcu_confirmation' : 0, 'last_pcu_reboot' : 0, 'last_download' : 0, 'run_level': 0, }}
    for node in FindbadNodeRecord.query.all():

        print >>sys.stderr, index, node.hostname, t2-t1
        index += 1
        t1 = time.time()
        if index > skip :
            for v in node.versions:

                d = v.__dict__
                (k,l) = dict_to_list(d, add_fields=add_fields, ignore_fields=ignore_fields)
                if not first_time:
                    if cmp(k, k_last) != 0:
                        print >>sys.stderr, "mismatching key lists"
                        print >>sys.stderr, k
                        print >>sys.stderr, k_last
                        for i in zip(k,k_last):
                            print >>sys.stderr, i
                        print >>sys.stderr, set(k) - set(k_last)
                        print >>sys.stderr, set(k_last) - set(k)
                        #sys.exit(1)
                        continue

                if d['timestamp'] > since_time:
                    if first_time:
                        print "timestamp_unix,%s" % ",".join(k[1:])
                        first_time = False


                    print "%s,%s" % (Time.dt_to_ts(d['timestamp']), ",".join(l[1:]))

                k_last = k
        t2=time.time()
