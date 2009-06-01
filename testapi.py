#!/usr/bin/python

import plc
import sys
import traceback

api = plc.getAuthAPI()

try:
	# Just try the first site returned by the call
	site = api.GetSites()[0]
	site_nodes = api.GetNodes(site['node_ids'])
	site_people = api.GetPersons(site['person_ids'])
	for node in site_nodes:
		network = api.GetInterfaces(node['interface_ids'])
	print "ok"
except:
	sys.stderr.write(traceback.format_exc())
	from nodecommon import email_exception
	email_exception()
	print "fail"
