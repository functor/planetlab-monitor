#!/usr/bin/python
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Stephen Soltesz <soltesz@cs.princeton.edu>
#
# $Id: monitor.py,v 1.7 2007/07/03 19:59:02 soltesz Exp $

import sys
import os
import getopt 
import thread
from threading import *
import time
import logging
import Queue
from sets import Set
# Global config options
from config import config
# daemonize and *pid
from util.process import * 

# Comon DB
import comon
# RT tickets
import rt
# Correlates input with policy to form actions
import policy
import soltesz
import plc

# Log to what 
LOG="./monitor.log"

# Time to refresh DB and remove unused entries
RTSLEEP=7200 #2hrs
# Time between policy enforce/update
#POLSLEEP=43200 #12hrs
POLSLEEP=10

# Global list of all running threads.  Any threads added to 
# list will be monitored.
runningthreads = {}
# Seconds between checking threads
WATCHSLEEP = 10
 
# Set up Logging
logger = logging.getLogger("monitor")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG, mode = 'a')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


"""
Launches threads and adds them to the runningthreads global list.
Assigns name for thread, starts.
"""
def startThread(fnct, name):
		runningthreads[name] = fnct
		runningthreads[name].setName(name)
		try:
			logger.info("Starting thread " + name)
			runningthreads[name].start()
		except Exception, err:
			logger.error("Thread: " + name + " " + error)


"""
Watches threads and catches exceptions.  Each launched thread is
watched and state is logged.
"""
class ThreadWatcher(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		while 1:
			self.checkThreads()
			time.sleep(WATCHSLEEP)

	def checkThreads(self):
		# Iterate through treads, compare with last running.
	 	for thread in runningthreads.keys():
			# If thread found dead, remove from queue
			#print "found %s" % thread
			if not runningthreads[thread].isAlive():
				logger.error("***********Thread died: %s**********" %(thread))
				del runningthreads[thread]
		return len(runningthreads.keys())


class Dummy(Thread):
	def __init__(self):
                Thread.__init__(self)

	def run(self):
		time.sleep(5)

def dict_from_nodelist(nl):
	d = {}
	for host in nl:
		h = host['hostname']
		d[h] = host
	return d

"""
Start threads, do some housekeeping, then daemonize.
"""
def main():
	# Defaults
	global status, logger
	global config

	#if not debug:
        #	daemonize()
        #	writepid("monitor")

	config = config()
	#config.parse_args()

	logger.info('Monitor Started')
	##########  VARIABLES   ########################################
	# Nodes to check. Queue of all sick nodes.
	toCheck = Queue.Queue()
	# Nodes that are sick w/o tickets
	sickNoTicket = Queue.Queue()
	# Comon DB of all nodes
	cdb = {}
	# RT DB
	tickets = {}
	# Nodes we've emailed.
	# host - > (type of email, time)
	emailed = {}

	#########  GET NODES    ########################################
	# TODO: get authoritative node list from PLC every PLCSLEEP seconds,
	# 		feed this into Comon.
	l_plcnodes = soltesz.if_cached_else(config.cachenodes, 
								"l_plcnodes", 
								lambda : plc.getNodes({'peer_id':None}))

	s_plcnodes = Set([x['hostname'] for x in l_plcnodes])

	# List of nodes from a user-provided file.
	if config.nodelist:
		file = config.nodelist
		nodelist = config.getListFromFile(file)
		l_nodelist = []
		print "Getting node info for hosts in: %s" % file
		for nodename in nodelist:
			if config.debug: print ".", ; sys.stdout.flush()
			l_nodelist += plc.getNodes({'hostname': nodename, 'peer_id':None})
		if config.debug: print ""
	
		s_usernodes = Set(nodelist)
		# nodes from PLC and in the user list.
		s_safe_usernodes   = s_plcnodes & s_usernodes
		s_unsafe_usernodes = s_usernodes - s_plcnodes
		if len(s_unsafe_usernodes) > 0 :
			for node in s_unsafe_usernodes:
				print "WARNING: User provided: %s but not found in PLC" % node

		l_nodes = filter(lambda x: x['hostname'] in s_safe_usernodes,l_plcnodes)
	else:
		l_nodes = l_plcnodes

	# Minus blacklisted ones..
	l_blacklist = soltesz.if_cached_else(1, "l_blacklist", lambda : [])
	l_ticket_blacklist = soltesz.if_cached_else(1,"l_ticket_blacklist",lambda : [])
	l_wl_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)
	# A handy dict of hostname-to-nodestruct mapping
	d_allplc_nodes = dict_from_nodelist(l_wl_nodes)

	#######  RT tickets    #########################################
	t = soltesz.MyTimer()
	ad_dbTickets = soltesz.if_cached_else(config.cachert, "ad_dbTickets", rt.rt_tickets)
	print "Getting tickets from RT took: %f sec" % t.diff() ; del t

	# TODO: get input nodes from findbad database, pipe into toCheck
	cm1 = read_findbad_db(d_allplc_nodes, toCheck)

	# Search for toCheck nodes in the RT db.
	rt1 = rt.RT(ad_dbTickets, tickets, toCheck, sickNoTicket, l_ticket_blacklist)
	# 	Kind of a hack. Cleans the DB for stale entries and updates db.
	#   (UNTESTED)
	#	rt5 = rt.RT(ad_dbTickets, tickets, toCheck, sickNoTicket)
	#	clean = Thread(target=rt5.cleanTickets)

	startThread(rt1,"rt1")
	#	startThread(rt5,"rt5")
	#	startThread(clean,"cleanrt5")

	# Actually digest the info and do something with it.
	pol = policy.Policy(cm1, sickNoTicket, emailed)
	# Start Sending Emails
	startThread(pol, "policy")


	tw = ThreadWatcher()
	while True:
		if tw.checkThreads() == 0:
			break
		time.sleep(WATCHSLEEP)

	logger.info('Monitor Exitting')
	#if not debug:
	#	removepid("monitor")

	# Store state of emails
	#pol.emailedStore("WRITE")
	soltesz.dbDump("ad_dbTickets")
	sys.exit(0)
	
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		#soltesz.dbDump("ad_dbTickets")
		sys.exit(0)
