#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $
#
# Get CoMon data, unsorted, in CSV, and create a huge hash.
#


import urllib2
import httplib
import time
import Queue 
import logging
from threading import *
#httplib.HTTPConnection.debuglevel = 1  

logger = logging.getLogger("monitor")

# Time between comon refresh
COSLEEP=1200

# CoMon
COMONURL = "http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeview"


class Comon(Thread): 
	"""
	cdb is the comon database (dictionary)
	all buckets is a queue of all problem nodes. This gets sent to rt to find
	tickets open for host. 
	"""
	def __init__(self, cdb, allbuckets):
		self.codata = cdb 
		self.updated = time.time()
		self.allbuckets = allbuckets
		self.comonbkts = {"down" : "resptime%20==%200%20&&%20keyok==null",
			"ssh": "sshstatus%20%3E%202h",
			"clock_drift": "drift%20%3E%201m",
			"dns": "dns1udp%20%3E%2080%20&&%20dns2udp%20%3E%2080",
			"filerw": "filerw%3E0",
			"dbg" : "keyok==0"}
		Thread.__init__(self)

	def __tohash(self,rawdata):
		# First line Comon returns is list of keys with respect to index
		keys = rawdata.readline().rstrip().split(", ")
		host = []
		hash = {}
		try:
			for line in rawdata.readlines():
				host = line.rstrip().split(", ")
				tmp = {}
				for i in range(1,len(keys)):
					tmp[keys[i]]=host[i]
				hash[host[0]]=tmp
			logger.debug("Retrieved %s hosts" % len(hash.keys()))
		except Exception, err:
			logger.debug("No hosts retrieved")	
			return {} 
		return hash

	# Update individual buckekts.  Hostnames only.
	def updatebkts(self):
		for (bkt,url) in self.comonbkts.items():
			logger.debug("COMON:  Updating bucket %s" % bkt)
			tmp = self.coget(COMONURL + "&format=formatcsv&select='" + url + "'").keys()
			setattr(self, bkt, tmp)

	# Update ALL node information
	def updatedb(self):
		# Get time of update
		self.updated = time.time()
		# Make a Hash, put in self.
		self.codata.update(self.coget(COMONURL + "&format=formatcsv"))

	def coget(self,url):
		rawdata = None
		try:
			coserv = urllib2.Request(url)
			coserv.add_header('User-Agent',
                		'PL_Monitor +http://monitor.planet-lab.org/')
			opener = urllib2.build_opener()
            		# Initial web get from summer.cs in CSV
			rawdata = opener.open(coserv)
		except urllib2.URLError, (err):
			print "Attempting %s" %COMONURL
			print "URL error (%s)" % (err)
			rawdata = None
		return self.__tohash(rawdata)

	# Push nodes that are bad (in *a* bucket) into q(allbuckets)
	def push(self):
		for bucket in self.comonbkts.keys():
			for host in getattr(self,bucket):
				self.allbuckets.put(host)

	def run(self):
		while 1:
			self.updatedb()
			self.updatebkts()
			self.push()
			time.sleep(COSLEEP)
 
	def __repr__(self):
	    return self

def main():
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)


	t = Queue.Queue()
	cdb = {}
	a = Comon(cdb,t)
	print a.comonbkts
	a.start()

	time.sleep(5)
	print a.down

	time.sleep(5)
	#print cdb
	for host in cdb.keys():
		if cdb[host]['keyok'] == "0":
			print("%s \t Bootstate %s nodetype %s kernver %s keyok %s" %(host, cdb[host]['bootstate'], cdb[host]['nodetype'], cdb[host]['kernver'], cdb[host]['keyok']))
	#time.sleep(3)
	#a.push()
	#print a.filerw
	#print a.coget(COMONURL + "&format=formatcsv&select='" + a.comonbkts['filerw'])

	os._exit(0)
if __name__ == '__main__':
	import os
        try:
                main()
        except KeyboardInterrupt:
                print "Killed.  Exitting."
                logger.info('Monitor Killed')
                os._exit(0)
