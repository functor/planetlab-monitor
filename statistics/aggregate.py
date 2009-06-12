#!/usr/bin/python


from monitor import database
import time
import sys

actall = database.dbLoad("act_all_080825")
agg = database.dbLoad("aggregatehistory")

for node in actall.keys():
	for record in actall[node]:
		if 'date_created' in record:
			t = record['date_created']
		elif 'time' in record:
			t = record['time']
		else:
			continue

		acttime = time.strftime("%Y-%m-%d", time.localtime(t)) 

		if acttime > '2007-11-06':
			if 'noop' in record['action']:
				if node in agg:
					for ntime,state in agg[node]:
						if state == 'BOOT':
							if ntime > acttime:
								if type(record['action']) == type([]):
									action = record['action'][0]
								else:
									action = record['action']
								print acttime, action, ntime, state, node

				#print time.strftime("%Y-%m-%d", time.localtime(t)), record['action'], node

#for node in agg:
#	for ntime,state in agg[node]:
#		if state == 'BOOT':
#			print ntime, state, node
