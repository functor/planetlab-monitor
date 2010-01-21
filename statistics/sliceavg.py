#!/usr/bin/python

import os
import sys

from monitor.wrapper import plc

from monitor.database.info.model import *

api = plc.cacheapi
api.AuthCheck()

# for each site, find total number of assigned slivers
# find median, high, low, average

site_list = []

for site in api.GetSites({'peer_id': None}):
	sl = api.GetSlices(site['slice_ids'])
	sliver_cnt = 0
	for slice in sl:
		sliver_cnt += len(slice['node_ids'])
	val = (site['login_base'], sliver_cnt, site['max_slices'])
	site_list.append(val)
	#print val

site_list.sort(lambda x,y: cmp(y[1], x[1]))
totals = 0
use_count = 0
print "loginbase,status,sliver_count,max_slices"
for i in site_list:
	if i[1] != 0: 
		h = HistorySiteRecord.get_by(loginbase=i[0])
		print "%10s,%s,%s,%s" % (i[0],h.status, i[1], i[2])
		use_count += 1
	totals += i[1]

site_avg = totals/len(site_list)

#print "high: %s %s" % site_list[0]
#print "low: %s %s" % site_list[-1]
#print "median: %s %s" % site_list[len(site_list)/2]
#print "used median: %s %s" % site_list[use_count/2]
#print "all avg: %s" % site_avg
#print "used avg: %s" % (totals/use_count)
#print "totals: %s" % totals 
#print "use_count: %s" % use_count
#print "site_count: %s" % len(site_list)
