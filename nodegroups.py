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
from sets import Set

from nodecommon import *
import soltesz
fb = soltesz.dbLoad("findbad")

parser = OptionParser()
parser.set_defaults(nodegroup="Alpha",
					node=None,
					nodelist=None,
					list=False,
					add=False,
					notng=False,
					delete=False,
					)
parser.add_option("", "--not", dest="notng", action="store_true", 
					help="All nodes NOT in nodegroup.")
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
if config.node or config.nodelist:
	if config.node: 
		hostlist = [ config.node ] 
	else: 
		hostlist = config.getListFromFile(config.nodelist)
	nodelist = api.GetNodes(hostlist)

	group_str = "Given"

else:
	ng = api.GetNodeGroups({'name' : config.nodegroup})
	nodelist = api.GetNodes(ng[0]['node_ids'])

	group_str = config.nodegroup

if config.notng:
	# Get nodegroup nodes
	ng_nodes = nodelist

	# Get all nodes
	all_nodes = api.GetNodes({'peer_id': None})
	
	# remove ngnodes from all node list
	ng_list = [ x['hostname'] for x in ng_nodes ]
	all_list = [ x['hostname'] for x in all_nodes ]
	not_ng_nodes = Set(all_list) - Set(ng_list)

	# keep each node that *is* in the not_ng_nodes set
	nodelist = filter(lambda x : x['hostname'] in not_ng_nodes, all_nodes)

hostnames = [ n['hostname'] for n in nodelist ]

# commands:
if config.list:
	print " ---- Nodes in the %s Node Group ----" % group_str
	i = 1
	for node in nodelist:
		print "%-2d" % i, 
		print nodegroup_display(node, fb)
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
