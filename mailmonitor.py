#!/usr/bin/python
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Stephen Soltesz <soltesz@cs.princeton.edu>
#
# $Id: monitor.py,v 1.7 2007/07/03 19:59:02 soltesz Exp $

import sys

from monitor import database
from monitor.wrapper import rt
from monitor.wrapper import plc
from monitor.policy import *
from monitor.database.info.model import *

api = plc.getAuthAPI()

def reboot(hostname):
	print "CALLING: mailmonitor.reboot(%s)" % hostname

	l_nodes = api.GetNodes(hostname)
	if len(l_nodes) == 0:
		raise Exception("No such host: %s" % hostname)
	
	q_blacklist = BlacklistRecord.query.all()

	l_blacklist = [ n.hostname for n in q_blacklist ]
	l_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)
	if len(l_nodes) == 0:
		raise Exception("Host removed via blacklist: %s" % hostname)

	mon = MonitorMergeDiagnoseSendEscellate(hostname, True)
	mon.run()

	return True

def main():
	for host in sys.argv[1:]:
		reboot(host)

if __name__ == '__main__':
	print "calling main"
	main()
