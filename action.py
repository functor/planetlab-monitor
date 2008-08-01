#!/usr/bin/python
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Stephen Soltesz <soltesz@cs.princeton.edu>
#
# $Id$

import sys
from threading import *
import time
import logging
import Queue
from sets import Set

# Global config options
from config import config
from optparse import OptionParser
parser = OptionParser()

parser.set_defaults(nodelist=None, 
					cachert=False, 
					cachenodes=False, 
					blacklist=None, 
					ticketlist=None)

parser.add_option("", "--nodelist", dest="nodelist",
					help="Read nodes to act on from specified file")
parser.add_option("", "--cachert", action="store_true",
					help="Cache the RT database query")
parser.add_option("", "--cachenodes", action="store_true",
					help="Cache node lookup from PLC")
parser.add_option("", "--ticketlist", dest="ticketlist",
					help="Whitelist all RT tickets in this file")
parser.add_option("", "--blacklist", dest="blacklist",
					help="Blacklist all nodes in this file")

config = config(parser)
config.parse_args()

# daemonize and *pid
#from util.process import * 

# RT tickets
import rt
# Correlates input with policy to form actions
import policy
import database
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

	logger.info('Action Started')
	print 'Action Started'

	#########  GET NODES    ########################################
	logger.info('Get Nodes from PLC')
	print "getnode from plc"
	l_plcnodes = database.if_cached_else(True,
								"l_plcnodes", 
								lambda : plc.getNodes({'peer_id':None}))

	s_plcnodenames = Set([x['hostname'] for x in l_plcnodes])

	# List of nodes from a user-provided file.
	if config.nodelist:
		file = config.nodelist
		nodelist = config.getListFromFile(file)
		#for node in nodelist:
		#	print "%s" % node
	
		s_usernodes = Set(nodelist)
		# SAFE nodes are in PLC and the list 
		s_safe_usernodes   = s_plcnodenames & s_usernodes
		# UNSAFE nodes are in list but not in PLC. i.e. ignore them.
		s_unsafe_usernodes = s_usernodes - s_plcnodenames
		if len(s_unsafe_usernodes) > 0 :
			for node in s_unsafe_usernodes:
				print "WARNING: User provided: %s but not found in PLC" % node

		l_nodes = filter(lambda x: x['hostname'] in s_safe_usernodes,l_plcnodes)
	else:
		l_nodes = l_plcnodes

	print "len of l_nodes: %d" % len(l_nodes)
	# Minus blacklisted ones..
	l_ticket_blacklist = database.if_cached_else(1,"l_ticket_blacklist",lambda : [])

	l_blacklist = database.if_cached_else(1, "l_blacklist", lambda : [])
	l_nodes  = filter(lambda x : not x['hostname'] in l_blacklist, l_nodes)

	#######  Get RT tickets    #########################################
	#logger.info('Get Tickets from RT')
	#t = commands.MyTimer()
	#ad_dbTickets = database.if_cached_else(config.cachert, "ad_dbTickets", rt.rt_tickets)
	#print "Getting tickets from RT took: %f sec" % t.diff() ; del t

	logger.info('Start Action thread')
	####### Action
	action = policy.Action( [node['hostname'] for node in l_nodes] )
	startThread(action,"action")


	tw = ThreadWatcher()
	while True:
		if tw.checkThreads() == 0:
			break
		time.sleep(WATCHSLEEP)

	logger.info('Action Exitting')
	sys.exit(0)
	
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Action Killed')
		sys.exit(0)
