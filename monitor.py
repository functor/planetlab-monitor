#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $

import sys
import os
import getopt 
import thread
from threading import *
import time
import logging
import Queue
# daemonize and *pid
from util.process import * 

# Comon DB
import comon
# RT tickets
import rt
# Correlates input with policy to form actions
import policy
# Email
import mailer
import emailTxt
# Defaults
debug = False 

# Log to what 
LOG="./monitor.log"

# Email defaults
MTA="localhost"
FROM="support@planet-lab.org"
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

def usage():
    print """
Usage: %s [OPTIONS]...

Options:
        -d, --debug             Enable debugging (default: %s)
        --status                Print memory usage statistics and exit
        -h, --help              This message
""".lstrip() % (sys.argv[0], debug)


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
			if not runningthreads[thread].isAlive():
				logger.error("Thread Died: %s" %(thread))
				del runningthreads[thread]


class Dummy(Thread):
	def __init__(self):
                Thread.__init__(self)

	def run(self):
		time.sleep(5)


"""
Start threads, do some housekeeping, then daemonize.
"""
def main():
	# Defaults
	global debug, status, logger

	try:
		longopts = ["debug", "status", "help"]
		(opts, argv) = getopt.getopt(sys.argv[1:], "dvf:s:ph", longopts)
	except getopt.GetoptError, err:
		print "Error: " + err.msg
		usage()
		sys.exit(1)

	for (opt, optval) in opts:
		if opt == "-d" or opt == "--debug":
			debug = True
		elif opt == "--status":
			#print summary(names)
			sys.exit(0)
		else:
			usage()
			sys.exit(0)

	#if not debug:
        #	daemonize()
        #	writepid("monitor")

	# Init stuff.  Watch Threads to see if they die.  Perhaps send email?
	logger.info('Monitor Started')
	startThread(ThreadWatcher(), "Watcher")
	# The meat of it.

	# Nodes to check
        bucket = Queue.Queue()
	# Comon DB of all nodes
	cdb = {}
	# Nodes that are down.  Use this to maintain DB;  cleanup.
        alldown = Queue.Queue()
	# RT DB
        tickets = {}

	# Get RT Tickets.
	# Event based.  Add to queue(bucket) and hosts are queried.
	rt1 = rt.RT(tickets, bucket)
	rt2 = rt.RT(tickets, bucket)
	rt3 = rt.RT(tickets, bucket)
	rt4 = rt.RT(tickets, bucket)
	rt5 = rt.RT(tickets, bucket)
	# Kind of a hack. Cleans the DB for stale entries and updates db.
	clean = Thread(target=rt5.cleanTickets)
	# Poll Comon.  Refreshes Comon data every COSLEEP seconds
	cm1 = comon.Comon(cdb, bucket)

	# Start Threads
	startThread(rt1,"rt1")
	startThread(rt2,"rt2")
	startThread(rt3,"rt3")
	startThread(rt4,"rt4")
	startThread(rt5,"rt5")
	startThread(clean,"cleanrt5")
	startThread(cm1,"rt5")
	time.sleep(10)

	# Actually digest the info and do something with it.
	pol = policy.Policy(cm1, tickets)

	while bucket.empty() == False:
		time.sleep(3)

	startThread(pol, "policy")
	time.sleep(3600)	
	
	#print runningthreads["RT"].ssh 

	logger.info('Monitor Exitted')
	#if not debug:
	#	removepid("monitor")
	os._exit(0)
	
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		os._exit(0)
