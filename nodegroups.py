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

from monitor import database
from monitor.database import FindbadNodeRecord
from monitor import util
from monitor.wrapper import plc
from monitor import parser as parsermodule

api = plc.getAuthAPI()

from nodequery import verify,query_to_dict,node_select
from monitor.common import *
from sets import Set

def main():

	parser = parsermodule.getParser(['nodesets'])
	parser.set_defaults( list=True,
						add=False,
                        nocolor=False,
						notng=False,
						delete=False,)

	parser.add_option("", "--not", dest="notng", action="store_true", 
						help="All nodes NOT in nodegroup.")
	parser.add_option("", "--nocolor", dest="nocolor", action="store_true", 
						help="Enable color")
	parser.add_option("", "--list", dest="list", action="store_true", 
						help="List all nodes in the given nodegroup")
	parser.add_option("", "--add", dest="add", action="store_true", 
						help="Add nodes to the given nodegroup")
	parser.add_option("", "--delete", dest="delete", action="store_true", 
						help="Delete nodes from the given nodegroup")

	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

	# COLLECT nodegroups, nodes and node lists
	if config.node or config.nodelist:
		if config.node: 
			hostlist = [ config.node ] 
		else: 
			hostlist = util.file.getListFromFile(config.nodelist)

		# NOTE: preserve order given in file.  Otherwise, return values are not in order
		# given to GetNodes
		nodelist = []
		for h in hostlist:
			nodelist += api.GetNodes(h)

		#nodelist = api.GetNodes(hostlist)
		group_str = "Given"

	elif config.site:
		site = api.GetSites(config.site)
		if len (site) > 0:
			site = site[0]
			nodelist = api.GetNodes(site['node_ids'])
		else:
			nodelist = []

		group_str = config.site

	elif config.nodeselect:
		hostlist = node_select(config.nodeselect)
		nodelist = api.GetNodes(hostlist)

		group_str = "selection"
		
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

	if config.add and config.nodegroup:
		for node in hostnames:
			print "Adding %s to %s nodegroup" % (node, config.nodegroup)
			api.AddNodeToNodeGroup(node, config.nodegroup)

	elif config.delete:
		for node in hostnames:
			print "Deleting %s from %s nodegroup" % (node, config.nodegroup)
			api.DeleteNodeFromNodeGroup(node, config.nodegroup)

	elif config.list:
		print " ---- Nodes in the %s Node Group ----" % group_str
		print "   Hostname                                   plc  obs     pcu     key         kernel                        last_contact, last change, comon uptime"
		i = 1
		for node in nodelist:
			print "%-2d" % i, 
			fbrec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==node['hostname']).order_by(FindbadNodeRecord.date_checked.desc()).first()
			fbdata = fbrec.to_dict()
			print nodegroup_display(node, fbdata, config)
			i += 1

	else:
		print "no other options supported."

if __name__ == "__main__":
	try:
		main()
	except IOError:
		pass
