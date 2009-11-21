#!/usr/bin/python

from monitor import database

sql = database.dbLoad("idTickets")
import sys

sortkeys = {}
print      "Queue     lastupdated     Status      Email          OwnerID Subject"
for id in sql.keys(): 
	#print sql[id].keys()
	#sys.exit(1)
	key = "%(queue)s-%(owner)s-%(status)s-%(lastupdated)s-%(email)-30s-%(subj)s" % sql[id]
	sortkeys[key] = "%(ticket_id)s %(queue)s %(lastupdated)s %(status)6s %(email)-25s %(owner)6s %(subj)26.26s https://rt.planet-lab.org/Ticket/Display.html?id=%(ticket_id)s" % sql[id]
	#sortkeys[key] = "%(ticket_id)s %(status)6s %(email)-30s %(lastupdated)s %(subj)s" % sql[id]

keys = sortkeys.keys()
keys.sort()
for key in keys:
	print sortkeys[key]
