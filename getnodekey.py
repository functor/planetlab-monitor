#!/usr/bin/python

import os
import sys
import string
import time
import soltesz
import plc

def main():

	l_nodes = [ 'planetlab4.inf.ethz.ch', 'planetlab-1.di.fc.ul.pt',
             'planetlab2.singaren.net.sg', 'planetlab2.nbgisp.com',
             'planetlab1.koganei.wide.ad.jp', 'planetlab2.koganei.wide.ad.jp',
             'planetlab1.citadel.edu', 'pl2.ucs.indiana.edu',
             'plab1.engr.sjsu.edu', 'plab2.engr.sjsu.edu',
             'planetlab1.iin-bit.com.cn', 'planetlab1.cs.virginia.edu',
             'planetlab1.info.ucl.ac.be', 'node-1.mcgillplanetlab.org', ]
	d_nodes = {}
	for host in l_nodes:
		n = plc.getNodes({'hostname' : host})
		d_nodes[host] = n
		#print n

	for host in d_nodes:
		ssh = soltesz.SSH('root', host)
		val = ssh.runE("grep NODE_KEY /tmp/planet.cnf")
		print "%s == %s" % (host, val)

	
if __name__ == '__main__':
	import os
	try:
		main()
	except Exception, error:
		print "Exception %s" % error
		sys.exit(0)
