#!/usr/bin/python

# Collect statistics from myops db on node downtimes.
# For every node that goes down we need:
#	* node down time
#	* node reboot time
#	* node notice time
#	* node up time

# then for each node, order events by time
#	for each event sequence extract sub-sequences like:
#		down xx up 		
#	for each such sub-sequence extract
#		time between down and up

from monitor.database.info.model import *
from math import *
import sys
from datetime import datetime

def find_next(history_list, from_index, node_status):
	list_len = len(history_list)
	for i in range(min(list_len-1, from_index), 0, -1):
		v = history_list[i]
		if v.status == node_status:
			return i

	return 0

def diff_time(t1, t2):
	d = t1-t2
	return d.days*60*60*24 + d.seconds

times = []
frequency = {}
count = 0
for index,node in enumerate(HistoryNodeRecord.query.all()):
	frequency[node.hostname] = 0

	if node.hostname == 'planetlab-02.kyushu.jgn2.jp':
		for h in node.versions:
			print h.last_checked, h.status

	#print "--"
	pairs = []
	i = len(node.versions)
	ret = find_next(node.versions, i, 'online')
	if ret == 0:
		print node.hostname
		print node.status
		print node.last_checked
		print node.last_changed
		#if count > 3: sys.exit(1)
		count += 1
		pairs.append((datetime.now(), node.versions[-1].last_checked))
	else:
		while i > 0:
			i = find_next(node.versions, i, 'down')
			i2 = find_next(node.versions, i, 'offline')
			if i == 0 and i2 == 0:
				break
			h1 = node.versions[i]
			#print i, h1.last_checked, h1.status
			h2 = node.versions[i2]
			#print i2, h2.last_checked, h2.status
			i = i2
			pairs.append((h1.last_checked,h2.last_checked))
			frequency[node.hostname] += 1

	# list of all times
	for p in pairs:
		times.append(diff_time(p[0],p[1]))

##frequency
def flip_key(hash):
	fk = {}
	for key in hash.keys():
		if hash[key] not in fk:
			fk[hash[key]] = []
		fk[hash[key]].append(key)
	return fk

freq = flip_key(frequency)
freq_list = freq.keys()
freq_list.sort()
for f in freq_list:
	print f, len(freq[f]), freq[f]

times.sort()
bins = {}
for i in range(0,200,1):
	step = i/2.0
	bins[step] = []
	
for t in times:
	t = t/60.0/60.0/24.0
	b = floor(t*2)/2.0
	bins[b].append(t)

keys = bins.keys()
keys.sort()
total = 0
for k in keys:
	total += len(bins[k])
	print k, len(bins[k]), total
