#!/usr/bin/python

import sys
sys.path.append('.')
sys.path.append('..')

from monitor.util.sshknownhosts import *

def main(hosts):
	k = SSHKnownHosts()
	if len (hosts) > 0:
		for host in hosts:
			k.updateDirect(host)
	else:
		k.updateAll()
	k.write()

if __name__ == '__main__':
	main(sys.argv[1:])
