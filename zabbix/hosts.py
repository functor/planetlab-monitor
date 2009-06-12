#!/usr/bin/python

from monitor.wrapper import plc
import os

api = plc.api

HOSTS_FILE="/etc/hosts"

def is_in_file(filename, pattern):
	f = os.popen("grep %s %s" % ( pattern, filename))
	content = f.read()
	if len(content) > 0:
		return True
	else:
		return False
def add_to_file(filename, data):
	os.system("echo '%s' >> %s" % (data, filename))
	print "echo '%s' >> %s" % (data, filename)

sites = api.GetSites({'login_base' : 'mlab*'}, ['node_ids'])
for s in sites:
	nodes = api.GetNodes(s['node_ids'], ['hostname', 'interface_ids'])
	for node in nodes:
		try:
			i = api.GetInterfaces({ 'interface_id' :  node['interface_ids'], 'is_primary' : True})
			print len(i), i
			print "%s %s" % (i[0]['ip'], node['hostname'])
			#if not is_in_file(HOSTS_FILE, node['hostname']):
			#	add_to_file(HOSTS_FILE, "%s %s" % (i[0]['ip'], node['hostname']))
		except:
			pass
