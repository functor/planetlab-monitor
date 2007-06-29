#!/usr/bin/python
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Stephen Soltesz <soltesz@cs.princeton.edu>
#
# $Id: monitor.py,v 1.5 2007/05/16 01:53:46 faiyaza Exp $

import sys
import os
import getopt 
import thread
from threading import *
import time
import logging
import Queue
# Global config options
from config import config
config = config()
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

# DAT
DAT="./monitor.dat"

# Email defaults
MTA="localhost"
FROM="support@planet-lab.org"
TECHEMAIL="tech-%s@sites.planet-lab.org"
PIEMAIL="pi-%s@sites.planet-lab.org"

# API
XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'

# Time between comon refresh
COSLEEP=300 #5mins
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

	#if not debug:
        #	daemonize()
        #	writepid("monitor")

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

	# List of nodes from a user-provided file.
	if config.userlist:
		file = config.userlist
		nodelist = config.getListFromFile(file)
		l_nodes = []
		print "Getting node info for hosts in: %s" % file
		for nodename in nodelist:
			l_nodes += plc.getNodes({'hostname': nodename})
	else:
		# Authoritative list of nodes from PLC
		l_nodes = soltesz.if_cached_else(config.cachenodes, "l_nodes", plc.getNodes)

	# Minus blacklisted ones..
	l_blacklist = soltesz.if_cached_else(1, "l_blacklist", lambda : [])
	l_wl_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)
	# A handy dict of hostname-to-nodestruct mapping
	d_allplc_nodes = dict_from_nodelist(l_wl_nodes)

	#######  RT tickets    #########################################
	t = soltesz.MyTimer()
	ad_dbTickets = soltesz.if_cached_else(config.cachert, "ad_dbTickets", rt.rt_tickets)
	print "Getting tickets from RT took: %f sec" % t.diff() ; del t

	# TODO: Refreshes Comon data every COSLEEP seconds
	cm1 = comon.Comon(cdb, d_allplc_nodes, toCheck)
	startThread(cm1,"comon")

	# TODO: make queues event based, not node based. 
	# From the RT db, add hosts to q(toCheck) for filtering the comon nodes.
	rt1 = rt.RT(ad_dbTickets, tickets, toCheck, sickNoTicket)
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
	soltesz.dbDump("l_blacklist")
	soltesz.dbDump("ad_dbTickets")
	sys.exit(0)
	
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		#soltesz.dbDump("l_blacklist")
		#soltesz.dbDump("ad_dbTickets")
		sys.exit(0)
