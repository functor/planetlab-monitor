#!/usr/bin/python


import plc
api = plc.getAuthAPI()

import parser as parsermodule
from sets import Set

from nodecommon import *
import database

def network_config_to_str(net):

	str = ""
	static_keys = ['method', 'ip', 'gateway', 'network', 'broadcast', 'netmask', 'dns1', 'dns2', 'mac', 'is_primary']
	for k in static_keys:
		str += "%15s == %s\n" % (k, net[k])

	return str
	

def main():
	fb = database.dbLoad("findbad")

	parser = parsermodule.getParser()
	parser.set_defaults(nodelist=None,
						list=False,
						add=False,
						notng=False,
						delete=False,
						)
	parser.add_option("", "--nodelist", dest="nodelist", metavar="list.txt", 
						help="Use all nodes in the given file for operation.")
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

	# COLLECT nodegroups, nodes and node lists
	for node in config.args:

		try:
			n = api.GetNodes(node)[0]
			#print n
			net = api.GetNodeNetworks(n['nodenetwork_ids'])[0]
			#print net

			node_keys = ['boot_state', 'key', 'last_updated', 'last_contact']
			for k in node_keys:
				if 'last' in k:
					print "%15s == %s" % (k, diff_time(n[k]))
				else:
					print "%15s == %s" % (k, n[k])

			print network_config_to_str(net)

			#for k in net.keys():
			#	print k, "==" , net[k]
		except:
			print "Error with %s" % node
			import traceback; print traceback.print_exc()
			pass

	# commands:
	if False:
		if config.list:
			print " ---- Nodes in the %s Node Group ----" % group_str
			i = 1
			for node in nodelist:
				print "%-2d" % i, 
				print nodegroup_display(node, fb)
				i += 1

		elif config.add and config.nodegroup:
			for node in hostnames:
				print "Adding %s to %s nodegroup" % (node, config.nodegroup)
				api.AddNodeToNodeGroup(node, config.nodegroup)

		elif config.delete:
			for node in hostnames:
				print "Deleting %s from %s nodegroup" % (node, config.nodegroup)
				api.DeleteNodeFromNodeGroup(node, config.nodegroup)

		else:
			print "no other options supported."

if __name__ == "__main__":
	try:
		main()
	except IOError:
		pass
