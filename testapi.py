#!/usr/bin/python

import sys
import traceback

from monitor.wrapper import plc

api = plc.getAuthAPI()
loginbase = sys.argv[1] # "princeton"

try:
	site = api.GetSites(loginbase)[0]
	site_nodes = api.GetNodes(site['node_ids'])
	site_people = api.GetPersons(site['person_ids'])
	for node in site_nodes:
		network = api.GetNodeNetworks(node['nodenetwork_ids'])
	print "ok"
except:
	sys.stderr.write(traceback.print_exc())
	print "fail"
