#!/usr/bin/python

import os
import sys
import string
import time
import plc

bwlimit = {}

def main():
	global bwlimit

	l_nodes = plc.getNodes()
	d_nodes = {}
	for host in l_nodes:
		h = host['hostname']
		d_nodes[h] = host

	for h in d_nodes:
		host = d_nodes[h]
		for nw_id in host['interface_ids']:
			l_nw = plc.getNodeNetworks({'interface_id': host['interface_ids']})
			bwlimit[h] = []
			for nw in l_nw:
				if nw['bwlimit'] != None and nw['bwlimit'] < 500000:
					bwlimit[h].append(nw['bwlimit'])
			if len(bwlimit[h]) == 0:
				del bwlimit[h]
	
	for host in bwlimit:
		print "%s %s" % (host, bwlimit[host])
			
	
if __name__ == '__main__':
	main()
