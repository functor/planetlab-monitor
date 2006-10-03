#!/usr/bin/python2

import os, sys, shutil
import MySQLdb
import string
import logging
import Queue
import time 
import comon
from threading import *

# RT database access constants file
RT_DB_CONSTANTS_PATH='/etc/planetlab/rt_db'

#Logging
logger = logging.getLogger("monitor")

# seconds between ticket update
RTSLEEP = 7200

def stripQuotes( str ):
	quotes= ["'",'"']
	if str[0] in quotes:
		str= str[1:]
	if str[len(str)-1] in quotes:
		str= str[:len(str)-1]
	return str


def readConstantsFile( file_path ):
	"""
	read a file consisting of lines of
	NAME=VALUE
	NAME='VALUE'
	NAME="VALUE"
	and return a dictionary of the values.

	blank lines, and lines starting with # (comments) are skipped
	"""

	contents= {}

	try:
		input_file= file(file_path,"r")
	except IOError, err:
		return None

	for line in input_file:
		if line[0] == "#":
			continue
		line= string.strip(line)
		if len(line) == 0:
			continue

		parts= string.split(line,"=",)
		if len(parts) <> 2:
			continue

		contents[parts[0]]= stripQuotes(parts[1])

	return contents



def open_rt_db():

	# read plc database passwords and connect
	rt_db_constants= readConstantsFile(RT_DB_CONSTANTS_PATH)
	if rt_db_constants is None:
		print "Unable to read database access constants from %s" % \
			  RT_DB_CONSTANTS_PATH
		return -1

	try:
		rt_db = MySQLdb.connect(host=rt_db_constants['RT_DB_HOST'],
				user=rt_db_constants['RT_DB_USER'],
		   		passwd=rt_db_constants['RT_DB_PASSWORD'],
				db=rt_db_constants['RT_DB_NAME'])
	except Error:
		print "Failed to connect to RT database"
		return -1

	return rt_db




def rt_tickets(hostname):
	db = open_rt_db()
	sql = """SELECT distinct Tk.id, Tk.Status, Tk.Subject
			 FROM Tickets AS Tk
			 JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId
			 JOIN Attachments AS At ON Tr.id=At.TransactionID
			 WHERE (At.Content LIKE '%%%s%%' OR
				At.Subject LIKE '%%%s%%') AND
				(Tk.Status = 'new' OR Tk.Status = 'open') AND
				Tk.Queue = 3
			 ORDER BY Tk.Status, Tk.LastUpdated DESC""" \
			 % (hostname,hostname)

	try:
		# create a 'cursor' (required by MySQLdb)
		c = db.cursor()
		c.execute(sql)
	except Exception, err:
		print "Could not execute RT query %s" %err
		return -1

	# fetch all rows (list of lists)
	raw = c.fetchall()

	# map list of lists (raw) to list of dicts (tickets) 
	# when int gets pulls from SQL into python ints are converted to LONG to
	# prevent overflow .. convert back
	tickets = map(lambda x: {"ticket_id":int(x[0]),
				"status":x[1],
				"subj":x[2]},
				raw)
	db.close()

	return tickets


'''
Finds tickets associated with hostnames.
The idea is if you give it an array of host names,
presumeably from comon's list of bad nodes, it starts
a few threads to query RT.  RT takes a while to return.

This is turning into a reinvention of DB design, which I dont believe in.
In an effort to keep things minimal, here's the basic algo:

Give list of hostnames to RT()
Finds tickets associate with new hostnames (not in dict(tickets)).
Remove nodes that have come backup. Don't care of ticket is closed after first query.
Another thread refresh tickets of nodes already in dict and remove nodes that have come up. 
'''
class RT(Thread):
	def __init__(self, tickets, bucket, target = None): 
		# Time of last update of ticket DB
		self.lastupdated = 0
		# Queue() is MP/MC self locking 
		self.bucket = bucket 
		#DB of tickets.  Name -> ticket
		self.tickets = tickets
		Thread.__init__(self,target = self.getTickets)

	# Takes node from alldownq, gets tickets.  
	# Thread that actually gets the tickets.
	def getTickets(self):
		while 1:
			host = self.bucket.get(block = True)
			if host == "None": break
			#if self.tickets.has_key(host) == False:
			logger.debug("Popping from q - %s" %host)
			tmp = rt_tickets(host)
			if tmp:
				logger.debug("Found tickets for %s" %host)
				self.tickets[host] = tmp 

	# Removes hosts that are no longer down.
	def remTickets(self):
		logger.debug("Removing stale entries from DB.") 
		prevdown = self.tickets.keys()

		currdown = []
		#BEGIN HACK.  This should be outside of this file. passed to class.
		cmn = comon.Comon(None, None)
        	cmn.updatebkts()
		for bucket in cmn.comonbkts.keys():
			for host in getattr(cmn,bucket):
				if host not in currdown: currdown.append(host)
		#END HACK

		# Actually do the comparison
		for host in prevdown:
			if host not in currdown:
				del self.tickets[host]
				logger.info("%s no longer down" % host)

	# Update Tickets
	def updateTickets(self):
		logger.info("Refreshing DB.")
		for host in self.tickets.keys():
			# Put back in Q to refresh
			self.bucket.put(host)

	def cleanTickets(self):
		while 1:
			self.remTickets()
			self.updateTickets()
			time.sleep(RTSLEEP)
	
def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	bucket = Queue.Queue() 
	tickets = {}
	a = RT(tickets, bucket)
	b = RT(tickets, bucket)
	c = RT(tickets, bucket)
	d = RT(tickets, bucket)
	e = RT(tickets, bucket)
	a.start()
	b.start()
	c.start()
	d.start()
	tmp = ('planetlab-2.vuse.vanderbilt.edu', 'planetlab-11.cs.princeton.edu', 'planet03.csc.ncsu.edu', 'planetlab1.pop-rj.rnp.br', 'planet1.halifax.canet4.nodes.planet-lab.org', 'planet1.cavite.nodes.planet-lab.org', 'ds-pl3.technion.ac.il', 'planetlab2.cs.purdue.edu', 'planetlab3.millennium.berkeley.edu', 'planetlab1.unl.edu', 'planetlab1.cs.colorado.edu', 'planetlab02.cs.washington.edu', 'orbpl2.rutgers.edu', 'planetlab2.informatik.uni-erlangen.de', 'pl2.ernet.in', 'neu2.6planetlab.edu.cn', 'planetlab-2.cs.uni-paderborn.de', 'planetlab1.elet.polimi.it', 'planetlab2.iiitb.ac.in', 'server1.planetlab.iit-tech.net', 'planetlab2.iitb.ac.in', 'planetlab1.ece.ucdavis.edu', 'planetlab02.dis.unina.it', 'planetlab-1.dis.uniroma1.it', 'planetlab1.iitb.ac.in', 'pku1.6planetlab.edu.cn', 'planetlab1.warsaw.rd.tp.pl', 'planetlab2.cs.unc.edu', 'csu2.6planetlab.edu.cn', 'pl1.ernet.in', 'planetlab2.georgetown.edu', 'planetlab1.cs.uchicago.edu') 
	for host in tmp:
		bucket.put(host)
	#et = Thread(target=e.pushHosts)	
	#et.start()
	time.sleep(15)
	print tickets.keys()
	time.sleep(15)
	print tickets.keys()
	time.sleep(15)
	print tickets.keys()
	#cmn = comon.Comon(cdb, bucket)
	#cmn.updatebkts()
	#for bucket in cmn.comonbkts.keys():
#		for host in getattr(cmn,bucket):
#			alldown.put(host)
#
	at = Thread(target=a.cleanTickets)
	at.start()
	time.sleep(15)
	print tickets.keys()
	os._exit(0)

if __name__ == '__main__':
    main()
