#!/usr/bin/python

# Read in the act_* databases and print out a human readable version

import sys
import time
import getopt
import database 
from monitor.wrapper import plccache

def main():

	sickdb = database.dbLoad(sys.argv[1])
	plcdb_hn2lb = plccache.plcdb_hn2lb
	s_nodenames = ""

	sorted_keys = sickdb.keys()
	sorted_keys.sort()
	print "anything"
	print len(sorted_keys)
	for loginbase in sorted_keys:
		print loginbase
		nodedict = sickdb[loginbase]['nodes']
		sort_nodekeys = nodedict.keys()
		sort_nodekeys.sort()
		print "%s :" % loginbase
		for nodename in sort_nodekeys:
			diag_node = sickdb[loginbase]['nodes'][nodename]
			keys = diag_node.keys()
			keys.sort()
			print nodename
			for k in keys:
				#print k
				if "message" not in k and "msg" not in k:
					print "\t'%s' : %s" % (k, diag_node[k])
			print "\t--"

	print s_nodenames

	
if __name__ == '__main__':
	main()
