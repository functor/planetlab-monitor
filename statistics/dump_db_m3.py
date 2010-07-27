#!/usr/bin/python

# Collect statistics from myops db on node downtimes.
# For every node that goes down we need:
#    * node down time
#    * node reboot time
#    * node notice time
#    * node up time

# then for each node, order events by time
#    for each event sequence extract sub-sequences like:
#        down xx up         
#    for each such sub-sequence extract
#        time between down and up

from monitor.database.info.model import *
from math import *
import sys
from datetime import datetime, timedelta
from monitor.common import *

if len(sys.argv) > 1 and sys.argv[1] == "--pcu":
    args = sys.argv[2:]
    find_pcu = True
else:
    args = sys.argv[1:]
    find_pcu = False


for index,node in enumerate(FindbadNodeRecord.query.all()):

    if find_pcu:
        if not node.plc_pcuid: 
            # NOTE: if we're looking for nodes with pcus, then skip the ones that don't have them.
            continue
    else:
        if node.plc_pcuid:
            # NOTE: if we're not looking for nodes with pcus, then skip those that have them
            continue

    print >>sys.stderr, index, node.hostname

    for v in node.versions:
        if find_pcu:
            # we should be guaranteed that the node has pcuids here, but it could be deleted or added later
            pcu = FindbadPCURecord.get_by(plc_pcuid=v.plc_pcuid)
            if pcu:
                v_pcu = pcu.get_as_of(v.timestamp)
                if v_pcu:
                    print "%s,%s,%s,%s,%s" % (Time.dt_to_ts(v.timestamp), v.hostname, v.observed_status, v_pcu.reboot_trial_status, v_pcu.plc_pcu_stats['model'])
            else:
                print "%s,%s,%s,%s,%s" % (Time.dt_to_ts(v.timestamp), v.hostname, v.observed_status, "NOPCU", "NONE")
                
        else:
            print "%s,%s,%s,%s,%s" % (Time.dt_to_ts(v.timestamp), v.hostname, v.observed_status, "NOPCU", "NONE")
