#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: comon.py,v 1.7 2007/07/03 19:59:02 soltesz Exp $
#
# Get CoMon data, unsorted, in CSV, and create a huge hash.
#


import urllib2
import httplib
import time
import Queue 
import logging
import pickle
from threading import *
#httplib.HTTPConnection.debuglevel = 1  

logger = logging.getLogger("monitor")

# Time between comon refresh
COSLEEP=1200

# CoMon
COMONURL = "http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeview"

# node type:
# null == <not in DB?>
# 	 0 == 
# 	 1 == Prod
# 	 2 == alpha
# 	 3 == beta

# boot state:
# 	0 == new
# 	1 == boot
#	2 == dbg
#	3 == rins
#	4 == ins

def _tohash(rawdata):
	# First line Comon returns is list of keys with respect to index
	try:
		keys = rawdata.readline().rstrip().split(", ")
		l_host = []
		hash = {}
		i_ignored = 0
		for line in rawdata.readlines():
			l_host = line.rstrip().split(", ")		# split the line on ', '
			hostname = l_host[0]
			hash[hostname] = {}
			for i in range(1,len(keys)):
				hash[hostname][keys[i]]=l_host[i]

	except Exception, err:
		logger.debug("No hosts retrieved")	
		return {} 
	return hash

def comonget(url):
	rawdata = None
	print "Getting: %s" % url
	try:
		coserv = urllib2.Request(url)
		coserv.add_header('User-Agent', 'PL_Monitor +http://monitor.planet-lab.org/')
		opener = urllib2.build_opener()
    		# Initial web get from summer.cs in CSV
		rawdata = opener.open(coserv)
	except urllib2.URLError, (err):
		print "Attempting %s" %COMONURL
		print "URL error (%s)" % (err)
		rawdata = None
	return _tohash(rawdata)


class Comon(Thread): 
	"""
	cdb is the comon database (dictionary)
	all buckets is a queue of all problem nodes. This gets sent to rt to find
	tickets open for host. 
	"""
	def __init__(self, cdb=None, d_allplc_nodes=None, q_allbuckets=None):

		self.accept_all_nodes = False

		if cdb == None:
			cdb = {}
		if d_allplc_nodes == None:
			self.accept_all_nodes = True # TODO :get from plc.

		self.codata = cdb 
		self.d_allplc_nodes = d_allplc_nodes
		self.updated = time.time()
		self.q_allbuckets = q_allbuckets
		#self.comon_buckets = {"down" : "resptime%20==%200%20&&%20keyok==null",
		#	"ssh": "sshstatus%20%3E%202h",
		#	"clock_drift": "drift%20%3E%201m",
		#	"dns": "dns1udp%20%3E%2080%20&&%20dns2udp%20%3E%2080",
		#	"filerw": "filerw%3E0",
		#	"dbg" : "keyok==0"}
		self.comon_buckets = {
			#"down" : "resptime==0&&keyok==null",
			#"ssh": "sshstatus > 2h",
			#"clock_drift": "drift > 1m",
			#"dns": "dns1udp>80 && dns2udp>80",
			#"filerw": "filerw > 0",
			#"all" : ""
			"dbg" : "keyok==0",
			}
		Thread.__init__(self)

	def __tohash(self,rawdata):
		# First line Comon returns is list of keys with respect to index
		keys = rawdata.readline().rstrip().split(", ")
		l_host = []
		hash = {}
		try:
			i_ignored = 0
			for line in rawdata.readlines():
				l_host = line.rstrip().split(", ")		# split the line on ', '
				hostname = l_host[0]
				add = False
				if self.accept_all_nodes:
					add=True
				else:
					if hostname in self.d_allplc_nodes:		# then we'll track it
						add = True

				if add:
					hash[hostname] = {}
					for i in range(1,len(keys)):
						hash[hostname][keys[i]]=l_host[i]
				else:
					i_ignored += 1

			print "Retrieved %s hosts" % len(hash.keys())
			print "Ignoring %d hosts" % i_ignored

			logger.debug("Retrieved %s hosts" % len(hash.keys()))
			logger.debug("Ignoring %d hosts" % i_ignored)
		except Exception, err:
			logger.debug("No hosts retrieved")	
			return {} 
		return hash

	# Update individual buckekts.  Hostnames only.
	def updatebuckets(self):
		for (bucket,url) in self.comon_buckets.items():
			logger.debug("COMON:  Updating bucket %s" % bucket)
			tmp = self.coget(COMONURL + "&format=formatcsv&select='" + url + "'").keys()
			setattr(self, bucket, tmp)

	# Update ALL node information
	def updatedb(self):
		# Get time of update
		self.updated = time.time()
		# Make a Hash, put in self.
		self.codata.update(self.coget(COMONURL + "&format=formatcsv"))

	def coget(self,url):
		rawdata = None
		print "Getting: %s" % url
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

	# Push nodes that are bad (in *a* bucket) into q(q_allbuckets)
	def push(self):
		#buckets_per_node = []
		#for bucket in self.comon.comon_buckets.keys():
		#	if (hostname in getattr(self.comon, bucket)):
		#		buckets_per_node.append(bucket)

		#loginbase = self.plcdb_hn2lb[hostname] # plc.siteId(node)

		#if not loginbase in self.sickdb:
		#	self.sickdb[loginbase] = [{hostname: buckets_per_node}]
		#else:
		#	self.sickdb[loginbase].append({hostname: buckets_per_node})


		print "calling Comon.push()"
		for bucket in self.comon_buckets.keys():
			#print "bucket: %s" % bucket
			for host in getattr(self,bucket):
				diag_node = {}
				diag_node['nodename'] = host
				diag_node['message'] = None
				diag_node['bucket'] = [bucket]
				diag_node['stage'] = ""
				#diag_node['ticket_id'] = ""
				diag_node['args'] = None
				diag_node['info'] = None
				diag_node['time'] = time.time()
				#print "host: %s" % host
				self.q_allbuckets.put(diag_node)

	def run(self):
		self.updatedb()
		self.updatebuckets()
		self.push()
		# insert signal that this is the final host
		self.q_allbuckets.put("None")
 
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
	#for i in a.comon_buckets: print "%s : %s" % ( i, a.comon_buckets[i])
	a.start()

	time.sleep(5)
	#for i in a.down: print i

	time.sleep(5)
	#print cdb
	for host in cdb.keys():
		#if cdb[host]['keyok'] == "0":
		# null implies that it may not be in PL DB.
		if  cdb[host]['bootstate'] != "null" and \
			cdb[host]['bootstate'] == "2" and \
			cdb[host]['keyok'] == "0":	
			print("%-40s \t Bootstate %s nodetype %s kernver %s keyok %s" % ( 
				host, cdb[host]['bootstate'], cdb[host]['nodetype'], 
				cdb[host]['kernver'], cdb[host]['keyok']))
	#	else:
	#		print("key mismatch at: %s" % host)
	#print a.codata['michelangelo.ani.univie.ac.at']
	#time.sleep(3)
	#a.push()
	#print a.filerw
	#print a.coget(COMONURL + "&format=formatcsv&select='" + a.comon_buckets['filerw'])

	#os._exit(0)
if __name__ == '__main__':
	import os
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		os._exit(0)
