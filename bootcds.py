#!/usr/bin/python

import os
import sys
import string
import time
import soltesz
import plc

bootcds = {}

def main():
	global bootcds

	l_nodes = plc.getNodes()
	d_nodes = {}
	for host in l_nodes:
		h = host['hostname']
		d_nodes[h] = host

	bootcds = soltesz.if_cached_else(1, "bootcds", lambda : {})
	for host in d_nodes:
		if not host in bootcds:
			ssh = soltesz.SSH('root', host)
			val = ssh.runE("F=/mnt/cdrom/bootme/ID;G=/usr/bootme/ID; if [ -f $F ] ; then cat $F ; else cat $G ; fi")
			print "%s == %s" % (host, val)
			bootcds[host] = val
		elif "timed out" in bootcds[host]:
			# Call again with a longer timeout!
			opts = soltesz.ssh_options
			opts['ConnectTimeout'] = '60'
			ssh = soltesz.SSH('root', host, opts)
			val = ssh.runE("F=/mnt/cdrom/bootme/ID;G=/usr/bootme/ID; if [ -f $F ] ; then cat $F ; else cat $G ; fi")
			print "TO: %s == %s" % (host, val)
			bootcds[host] = val
			

	soltesz.dbDump("bootcds", bootcds)
	
if __name__ == '__main__':
	import os
	try:
		main()
	except Exception:
		print "Saving data... exitting."
		soltesz.dbDump("bootcds", bootcds)
		sys.exit(0)
