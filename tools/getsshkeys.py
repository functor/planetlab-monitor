#!/usr/bin/python

import sys
from monitor.util.sshknownhosts import SSHKnownHosts

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
