#!/usr/bin/python


import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

from optparse import OptionParser
from sets import Set

from nodecommon import *
import soltesz

def main():
	from config import config
	fb = soltesz.dbLoad("findbad")

	parser = OptionParser()
	parser.set_defaults(nodelist=None,
						list=False,
						add=False,
						notng=False,
						delete=False,
						)
	parser.add_option("", "--nodelist", dest="nodelist", metavar="list.txt", 
						help="Use all nodes in the given file for operation.")
	config = config(parser)
	config.parse_args()

	# COLLECT nodegroups, nodes and node lists
	for node in config.args:

		try:
			n = api.GetNodes(node)[0]
			print n
			net = api.GetNodeNetworks(n['nodenetwork_ids'])[0]
			print net

			node_keys = ['boot_state', 'key', 'last_updated', 'last_contact']
			for k in node_keys:
				if 'last' in k:
					print "%15s == %s" % (k, diff_time(net[k]))
				else:
					print "%15s == %s" % (k, net[k])

			static_keys = ['method', 'ip', 'gateway', 'network', 'broadcast', 'netmask', 'dns1', 'dns2', 'mac', 'is_primary']
			for k in static_keys:
				print "%15s == %s" % (k, net[k])

			#for k in net.keys():
			#	print k, "==" , net[k]
		except:
			print "Error with %s" % node
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
