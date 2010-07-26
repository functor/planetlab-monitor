#!/usr/bin/python

# Collect statistics from myops db on site failures and recovery times.
# For every site that goes down we need:
#    * site down time
#    * site up time

from monitor.database.info.model import *
from math import *
import sys
from datetime import datetime, timedelta
from monitor.common import *

d_start = datetime(2009, 6, 10)
d_end = datetime.now()

#print "date_checked,date_changed,timestamp,last_changed,sitename,status"
print "date,t,sitename,status,length"

if len(sys.argv[1:]) > 0:
    l = enumerate(sys.argv[1:])
    l = [(i,HistorySiteRecord.get_by(loginbase=lb)) for i,lb in l ]
else:
    l = enumerate(HistorySiteRecord.query.all())

for index,site in l:
    d = d_start

    time_at_level = 0
    not_printed = True
    start = False

    last_level = site.versions[0].penalty_level
    last_time = site.versions[0].timestamp

    length = len(site.versions)
    for i,v in enumerate(site.versions[1:]):

        if v.nodes_up < 2 and not start:
            last_time = v.timestamp
            start = True

        if v.nodes_up >= 2 and start and v.penalty_level == 0:
            time_at_level = Time.dt_to_ts(v.timestamp) - Time.dt_to_ts(last_time)
            print "%s,%s,%s,%s,%s" % (Time.dt_to_ts(v.timestamp), 
                v.timestamp.strftime("%Y-%m-%d"), v.loginbase, last_level, time_at_level)
            start = False

        if last_level != v.penalty_level:
            last_level = v.penalty_level

        #print i,length-2, last_level != v.penalty_level, i == length-2
        #if last_level != v.penalty_level or i == length-2:
        #if last_level > v.penalty_level: # or i == length-2:
            #print "last_time ", last_time
            #print "diff times", v.timestamp
            #print "timestamp ", v.timestamp 
            #print "lastchange", v.last_changed
        #    time_at_level = Time.dt_to_ts(v.timestamp) - Time.dt_to_ts(last_time)
        #    print "%s,%s,%s,%s,%s" % (Time.dt_to_ts(v.timestamp), 
        #        v.timestamp.strftime("%Y-%m-%d"), v.loginbase, last_level, time_at_level)

        #if last_level != v.penalty_level:
        #    #print "levels mis-match", last_level, v.penalty_level
        #    last_level = v.penalty_level
        #    if last_level != 2:
        #    #    print "recording time", v.timestamp
        #        last_time = v.timestamp


        
    #while d < d_end:
#
#        v = site.get_as_of(d)
#        if v:
#            print "%s,%s,%s,%s" % (Time.dt_to_ts(d),
#                    d.strftime("%Y-%m-%d"), v.loginbase, v.penalty_level)
##
#        d += timedelta(1)

