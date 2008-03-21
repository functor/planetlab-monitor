#!/usr/bin/python

import os
import sys
import string
import time
import soltesz
import plc

def main():

	l_nodes = plc.getNodes() 
	d_nodes = {}
	nokey_list = []
	for host in l_nodes:
		name = host['hostname']
		d_nodes[name] = host

	f = open("known_hosts", 'w')
	for host in d_nodes:
		node = d_nodes[host]
		key = node['ssh_rsa_key']
		if key == None:
			nokey_list += [node]
		else:
			l_nw = plc.getNodeNetworks({'nodenetwork_id':node['nodenetwork_ids']})
			if len(l_nw) > 0:
				ip = l_nw[0]['ip']
				key = key.strip()
				# TODO: check for '==' at end of key.
				if key[-1] != '=':
					print "Host with corrupt key! for %s %s" % (node['boot_state'], node['hostname'])
				s_date = time.strftime("%Y/%m/%d_%H:%M:%S",time.gmtime(time.time()))
				print >>f, "%s,%s %s %s" % (host,ip, key, "PlanetLab_%s" % (s_date))
	f.close()

	for node in nokey_list:
		print "%5s %s" % (node['boot_state'], node['hostname'])
	
if __name__ == '__main__':
	import os
	main()
