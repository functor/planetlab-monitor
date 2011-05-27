#!/usr/bin/python

from monitor.database.info.model import *
import time
import sys

sumdata = {}
sumdata['nodes'] = {}
sumdata['sites'] = {}
sumdata['pcus'] = {}

def summarize(query, type):
	for o in query:
		if o.status not in sumdata[type]:
			sumdata[type][o.status] = 0
		sumdata[type][o.status] += 1

time_str = time.strftime("%m/%d/%y+%H:%M")

if len(sys.argv) == 1:
	print "For use in conjunction with add-google-record.py"
	print "Usage: %s <nodes|sites>" % sys.argv[0]
	sys.exit(1)

elif sys.argv[1] == "sites":

	site_type_list = ['date', 'good', 'offline', 'down', 'online', 'new']

	for k in site_type_list:
		sumdata['sites'][k]=0 

	fbquery = HistorySiteRecord.query.all()
	summarize(fbquery, 'sites')
	sumdata['sites']['date'] = time_str
	for f in sumdata['sites']:
		sumdata['sites'][f] = str(sumdata['sites'][f])

	l = ",".join(site_type_list)
	v = ",".join([ sumdata['sites'][k] for k in site_type_list ])
	print "--labels=%s --values=%s" % ( l, v )

elif sys.argv[1] == "nodes":

	node_type_list = ['date', 'good', 'offline', 'down', 'online', 'disabled', 'failboot', 'safeboot']
	for k in node_type_list:
		sumdata['nodes'][k]=0 
	fbquery = HistoryNodeRecord.query.all()
	summarize(fbquery, 'nodes')
	sumdata['nodes']['date'] = time_str
	for f in sumdata['nodes']:
		sumdata['nodes'][f] = str(sumdata['nodes'][f])

	l = ",".join(node_type_list)
	v = ",".join([ sumdata['nodes'][k] for k in node_type_list ])
	print "--labels=%s --values=%s" % ( l, v )


#row.content
#row.Push()
#row.Pull()
