#!/usr/bin/python

from monitor.wrapper import plc
import os
import sys
import time

if len(sys.argv) <= 1: 
	print "usage: leave.py <loginbase>"
	sys.exit(1)


for loginbase in sys.argv[1:]:
	site = plc.getSites({'login_base': loginbase}, ['person_ids', 'ext_consortium_id'])
	if len(site) < 1:
		print "no sites found"
		sys.exit(1)
	person_ids = site[0]['person_ids']
	persons = plc.getPersons(person_ids,  ['email', 'first_name', 'last_name', 'title', 'roles'])

	name = None
	for person in persons:
		if "pi" in person['roles']:
			name = "%s %s %s (%s)" % (person['title'], person['first_name'], person['last_name'], person['email'])

	if not name:
		print "no pis at %s" % loginbase
		sys.exit(1)

	date = time.strftime("%Y/%m/%d", time.gmtime(time.time()))

	print "loginbase :   date     : name 						: ext_consortium_id"
	print "%9s : %10s : %s : %s" % (loginbase, date, name, site[0]['ext_consortium_id'])
