#!/usr/bin/python

from monitor.wrapper import plc

api = plc.api

sites = api.GetSites({'login_base' : 'princeton'}, ['person_ids', 'name'])
for s in sites:
	persons = api.GetPersons(sites[0]['person_ids'], ['email' , 'first_name', 'last_name',])
	for p in persons:
		print "%s,%s %s,%s" % (p['email'], p['first_name'], p['last_name'], s['name'])
