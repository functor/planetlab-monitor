#!/usr/bin/python

# Collect statistics from myops db on node downtimes.
# For every site that goes down we need:

from monitor.database.info.model import *
from math import *
import sys

def find_next(history_list, from_index, status):
	list_len = len(history_list)
	#for i in range(min(list_len-1, from_index), 0, -1):
	for i in range(max(0, from_index), list_len, 1):
		v = history_list[i]
		if status in v.action_type:
			return i

	return list_len

def diff_time(t1, t2):
	d = t1-t2
	return d.days*60*60*24 + d.seconds


times = []
for index,site in enumerate(HistorySiteRecord.query.all()):

	acts = ActionRecord.query.filter_by(loginbase=site.loginbase).order_by(ActionRecord.date_created.asc()).all()
	act_len = len(acts)
	print site.loginbase, act_len

	#for a in acts:
	#	print a.date_created, a.loginbase, a.action_type
	i=0
	pairs = []
	while i < act_len:
		i = find_next(acts, i, 'notice')
		i2= find_next(acts, i, 'pause_penalty')
		print i, i2
		if i == act_len or i2 == act_len:
			break

		print i, i2
		a1 = acts[i]
		print a1.date_created, a1.loginbase, a1.action_type
		a2 = acts[i2]
		print a2.date_created, a2.loginbase, a2.action_type
		i = i2
		pairs.append((a1,a2))
	
#	# list of all times
#
	for p in pairs:
		if diff_time(p[1].date_created,p[0].date_created) < 0:
			print "fuck!"
			sys.exit(1)
		times.append(diff_time(p[1].date_created,p[0].date_created))


times.sort()
bins = {}
for i in range(0,200,1):
	step = i/2.0
	bins[step] = []
	
for t in times:
	t = t/60/60/24
	b = floor(t*2)/2.0
	bins[b].append(t)

keys = bins.keys()
keys.sort()
total = 0
for k in keys:
	total += len(bins[k])
	print k, len(bins[k]), total
