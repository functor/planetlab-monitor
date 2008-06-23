#!/usr/bin/python
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Stephen Soltesz <soltesz@cs.princeton.edu>
#
# $Id: monitor.py,v 1.7 2007/07/03 19:59:02 soltesz Exp $

import soltesz

from monitor_policy import *
import rt

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

def reboot(hostname):

	l_nodes = api.GetNodes(hostname)
	if len(l_nodes) == 0:
		raise Exception("No such host: %s" % hostname)
	
	l_blacklist = soltesz.if_cached_else(1, "l_blacklist", lambda : [])
	l_ticket_blacklist = soltesz.if_cached_else(1,"l_ticket_blacklist",lambda : [])

	l_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)
	if len(l_nodes) == 0:
		raise Exception("Host removed via blacklist: %s" % hostname)

	ad_dbTickets = soltesz.if_cached_else_refresh(True, False, "ad_dbTickets", lambda : [])
	if ad_dbTickets == None:
		raise Exception("Could not find cached dbTickets")

	#print "merge"
	merge = Merge( [node['hostname'] for node in l_nodes])
	record_list = merge.run()
	#print "rt"
	rt = RT(record_list, ad_dbTickets, l_ticket_blacklist)
	record_list = rt.run()
	#print "diagnose"
	diag = Diagnose(record_list)
	diagnose_out = diag.run()
	#print diagnose_out
	#print "action"
	action = Action(diagnose_out)
	action.run()

	return True

def reboot2(hostname):
	l_nodes = api.GetNodes(hostname)
	if len(l_nodes) == 0:
		raise Exception("No such host: %s" % hostname)
	
	l_blacklist = soltesz.if_cached_else(1, "l_blacklist", lambda : [])
	l_ticket_blacklist = soltesz.if_cached_else(1,"l_ticket_blacklist",lambda : [])

	l_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)
	if len(l_nodes) == 0:
		raise Exception("Host removed via blacklist: %s" % hostname)

	ad_dbTickets = soltesz.if_cached_else_refresh(True, False, "ad_dbTickets", lambda : None)
	if ad_dbTickets == None:
		raise Exception("Could not find cached dbTickets")


	args = {}
	args['hostname'] = "%s" % hostname
	args['hostname_list'] = "%s" % hostname
	args['loginbase'] = plc.siteId(hostname)

	m = PersistMessage(hostname, "Please Update Boot Image for %s" % hostname,
							mailtxt.newalphacd_one[1] % args, True, db='bootcd_persistmessages')
	
	#print "merge"
	merge = Merge( [node['hostname'] for node in l_nodes])
	record_list = merge.run()
	#print "rt"
	rt = RT(record_list, ad_dbTickets, l_ticket_blacklist)
	record_list = rt.run()
	#print "diagnose"
	diag = Diagnose(record_list)
	diagnose_out = diag.run()
	#print diagnose_out
	#print "action"
	action = Action(diagnose_out)
	action.run()

	return True


def main():
	pass

if __name__ == '__main__':
	main()
