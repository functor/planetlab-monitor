#!/usr/bin/python

# This script is used to manipulate the operational state of nodes in
# different node groups.  These are basically set operations on nodes via the
# PLC api.
# 
# Take the ng name as an argument....
# optionally, 
#  * restart them all.
#  * Set some or all in the set to rins.
#  * get a list of nodes in the Alpha nodegroup.
# 
# Given a nodelist, it could tag each one with a nodegroup name.
#  * 

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

from config import config
from optparse import OptionParser

import soltesz
fb = soltesz.dbLoad("findbad")

def get_current_state(fbnode):
	state = fbnode['state']
	l = state.lower()
	if l == "debug": return 'dbg'
	return l

parser = OptionParser()
parser.set_defaults(nodegroup="Alpha",
					node=None,
					nodelist=None,
					list=False,
					add=False,
					delete=False,
					)
parser.add_option("", "--nodegroup", dest="nodegroup", metavar="NodegroupName",
					help="Specify a nodegroup to perform actions on")
parser.add_option("", "--list", dest="list", action="store_true", 
					help="List all nodes in the given nodegroup")
parser.add_option("", "--add", dest="add", action="store_true", 
					help="Add nodes to the given nodegroup")
parser.add_option("", "--delete", dest="delete", action="store_true", 
					help="Delete nodes from the given nodegroup")
parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
					help="A single node name to add to the nodegroup")
parser.add_option("", "--nodelist", dest="nodelist", metavar="list.txt", 
					help="Use all nodes in the given file for operation.")
config = config(parser)
config.parse_args()

# COLLECT nodegroups, nodes and node lists
ng = api.GetNodeGroups({'name' : config.nodegroup})
nodelist = api.GetNodes(ng[0]['node_ids'])
hostnames = [ n['hostname'] for n in nodelist ]

if config.node or config.nodelist:
	if config.node: hostnames = [ config.node ] 
	else: hostnames = config.getListFromFile(config.nodelist)

# commands:
if config.list:
	print " ---- Nodes in the %s Node Group ----" % config.nodegroup
	i = 0
	for node in nodelist:
		print "%-2d" % i, 
		if node['hostname'] in fb['nodes']:
			node['current'] = get_current_state(fb['nodes'][node['hostname']]['values'])
		else:
			node['current'] = 'none'
		print "%(hostname)-38s %(boot_state)5s %(current)5s %(key)s" % node
		i += 1

elif config.add:
	for node in hostnames:
		print "Adding %s to %s nodegroup" % (config.node, config.nodegroup)
		api.AddNodeToNodeGroup(config.node, config.nodegroup)

elif config.delete:
	for node in hostnames:
		print "Deleting %s from %s nodegroup" % (config.node, config.nodegroup)
		api.DeleteNodeFromNodeGroup(config.node, config.nodegroup)

else:
	print "no other options supported."
