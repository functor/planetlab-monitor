#!/usr/bin/python

import sys
import traceback

from monitor.wrapper import plc

api = plc.getAuthAPI()

try:
	# Just try the first site returned by the call
	site = api.GetSites()[0]
	site_nodes = api.GetNodes(site['node_ids'])
	site_people = api.GetPersons(site['person_ids'])
	for node in site_nodes:
		network = api.GetNodeNetworks(node['nodenetwork_ids'])
	print "ok"
except:
	sys.stderr.write(traceback.format_exc())
	print "fail"
