#!/usr/bin/python

# Read in the act_* databases and print out a human readable version

import sys
import time
import getopt
import soltesz

def main():

	act_all = soltesz.dbLoad(sys.argv[1])
	plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")
	s_nodenames = ""
	sickdb = {}

	sorted_keys = act_all.keys()
	sorted_keys.sort()
	for nodename in sorted_keys:
		diag_nodelist = act_all[nodename]
		lb = plcdb_hn2lb[nodename]
		if lb not in sickdb:
			sickdb[lb] = {}
		sickdb[lb][nodename] = diag_nodelist

	sorted_keys = sickdb.keys()
	sorted_keys.sort()
	for loginbase in sorted_keys:
		nodedict = sickdb[loginbase]
		sort_nodekeys = nodedict.keys()
		sort_nodekeys.sort()
		print "%s :" % loginbase
		for nodename in sort_nodekeys:
			if len(act_all[nodename]) == 0:
				print "%20s : %-40s has no events" % (loginbase, nodename)
			else:
				l_ev = act_all[nodename]
				print "    %s" % nodename
				for diag_node in l_ev:
					#s_time=time.strftime("%Y/%m/%d %H:%M:%S",time.gmtime(ev[1]))
					keys = diag_node.keys()
					keys.sort()
					for k in keys:
						if "message" not in k and "msg" not in k:
							print "\t'%s' : %s" % (k, diag_node[k])
					print "\t--"

	print s_nodenames

	
if __name__ == '__main__':
	main()
