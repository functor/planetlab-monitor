#!/usr/bin/python

from monitor.model import *

sql = database.dbLoad("idTickets")
for db in ["monitor", "pcu", "bootcd", "hardware", "unknown", 
		  "suspect", "baddns", "nodenet", "nodeid"]:
	db = "%s_persistmessages" % db
	#print db
	try:
		pm = database.dbLoad(db)
	except:
		continue
	for host in pm.keys():
		m = pm[host]
		id = str(m.ticket_id)
		if m.ticket_id > 0:
			if id in sql:
				print "%s %6s %s" % (m.ticket_id, sql[id]['status'], host)
			else:
				print "%s closed %s" % ( m.ticket_id, host)
