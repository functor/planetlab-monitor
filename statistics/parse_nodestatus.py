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

recent_node_ts = {}
recent_node_states = {}
last_node_state = {}
last_node_ts = {}
print "ts,host,status,pcustatus,model,length"

while True:
    line = sys.stdin.readline()
    if not line:
        break
    line = line.strip()
    # NOTE assumes ts are ordered.
    try:
        (ts, host, state, pcu, pcumodel) = line.split(',')
    except:
        print >>sys.stderr, "EXCEPTION:", line
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if line[0] == ',':
                pcumodel = line[1:]
                break
        #sys.exit(1)

    ts = int(float(ts))
    add(recent_node_states, host, state)
    add(recent_node_ts, host, ts)

    if host not in last_node_state:
        last_node_state[host] = "UNKNOWN"
        last_node_ts[host] = ts
        
    if ( (in_hard_state(recent_node_states[host]) and stateof(recent_node_states[host]) == "DOWN") or \
        not in_hard_state(recent_node_states[host]) ) and \
       last_node_state[host] != stateof(recent_node_states[host]):

        if stateof(recent_node_states[host]) == "DOWN":
            ts = recent_node_ts[host][-1]   # get earliest time down
        print "%s,%s,%s,%s,%s,%s" % (ts, host, stateof(recent_node_states[host]), pcu, pcumodel, ts-last_node_ts[host] )
        last_node_state[host] = stateof(recent_node_states[host])
        last_node_ts[host] = ts


