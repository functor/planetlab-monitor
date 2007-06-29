#!/usr/bin/python2

import os, sys, shutil
import MySQLdb
import string
import logging
import Queue
import time 
import re
import comon
import soltesz
from threading import *
import config

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
	except Exception, err:
		print "Failed to connect to RT database: %s" %err
		return -1

	return rt_db




def rt_tickets():
	db = open_rt_db()
#	sql = """SELECT distinct Tk.id, Tk.Status, Tk.Subject
#			 FROM Tickets AS Tk
#			 JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId
#			 JOIN Attachments AS At ON Tr.id=At.TransactionID
#			 WHERE (At.Content LIKE '%%%s%%' OR
#				At.Subject LIKE '%%%s%%') AND
#				(Tk.Status = 'new' OR Tk.Status = 'open') AND
#				Tk.Queue = 3 OR Tk.Queue = 19 
#			 ORDER BY Tk.Status, Tk.LastUpdated DESC""" \
#			 % (hostname,hostname)
#	sql = """SELECT distinct Tk.id, Tk.Status, Tk.Subject
#			 FROM Tickets AS Tk
#			 JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId
#			 JOIN Attachments AS At ON Tr.id=At.TransactionID
#			 WHERE (At.Content LIKE '%%%s%%' OR
#				At.Subject LIKE '%%%s%%') AND
#				(Tk.Status = 'new' OR Tk.Status = 'open')
#			 ORDER BY Tk.Status, Tk.LastUpdated DESC""" \
#			 % (hostname,hostname)

	# Queue == 10 is the spam Queue in RT.
	sql = """SELECT distinct Tk.id, Tk.Status, Tk.Subject, At.Content
			 FROM Tickets AS Tk, Attachments AS At 
			 JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId  
			 WHERE Tk.Queue != 10 AND Tk.id > 10000 AND 
			 	   Tr.id=At.TransactionID AND (Tk.Status = 'new' OR Tk.Status = 'open')"""

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
				"subj":str(x[2]),
				"content":str(x[3])},
				raw)
	db.close()

	return tickets

def is_host_in_rt_tickets(host, ad_rt_tickets):
	# ad_rt_tickets is an array of dicts, defined above.
	if len(ad_rt_tickets) == 0:
		return (False, None)
	
	d_ticket = ad_rt_tickets[0]
	if not ('ticket_id' in d_ticket and 'status' in d_ticket and 
			'subj' in d_ticket and 'content' in d_ticket):
		logger.debug("RT_tickets array has wrong fields!!!")
		return (False, None)

	#logger.debug("Searching all tickets for %s" % host)
	def search_tickets(host, ad_rt_tickets):
		# compile once for more efficiency
		re_host = re.compile(host)
		for x in ad_rt_tickets:
			if re_host.search(x['subj'], re.MULTILINE|re.IGNORECASE) or \
			   re_host.search(x['content'], re.MULTILINE|re.IGNORECASE):
				logger.debug("\t ticket %d has %s" % (x['ticket_id'], host))
				return (True, x)
		logger.debug("\t noticket -- has %s" % host)
		return (False, None)

	# This search, while O(tickets), takes less than a millisecond, 05-25-07
	#t = soltesz.MyTimer()
	ret = search_tickets(host, ad_rt_tickets)
	#del t

	return ret


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
	def __init__(self, dbTickets, tickets, qin_toCheck, qout_sickNoTicket, target = None): 
		# Time of last update of ticket DB
		self.dbTickets = dbTickets
		self.lastupdated = 0
		# Check host in queue.  Queue populated from comon data of sick. 
		self.qin_toCheck = qin_toCheck
		# Result of rt db query.  Nodes without tickets that are sick.
		self.qout_sickNoTicket = qout_sickNoTicket 
		#DB of tickets.  Name -> ticket
		self.tickets = tickets
		Thread.__init__(self,target = self.getTickets)

	# Takes node from qin_toCheck, gets tickets.  
	# Thread that actually gets the tickets.
	def getTickets(self):
		self.count = 0
		while 1:
			diag_node = self.qin_toCheck.get(block = True)
			if diag_node == "None": 
				print "RT processed %d nodes with noticket" % self.count
				logger.debug("RT filtered %d noticket nodes" % self.count)
				self.qout_sickNoTicket.put("None")
				break
			else:
				host = diag_node['nodename']
				(b_host_inticket, r_ticket) = is_host_in_rt_tickets(host, self.dbTickets)
				if b_host_inticket:
					logger.debug("RT: found tickets for %s" %host)
					diag_node['stage'] = 'stage_rt_working'
					diag_node['ticket_id'] = r_ticket['ticket_id']
					self.tickets[host] = r_ticket
				else:
					#logger.debug("RT: no tix for %s" %host)
					#print "no tix for %s" % host
					self.count = self.count + 1

				# process diag_node for either case
				self.qout_sickNoTicket.put(diag_node) 

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
				logger.info("RT: %s no longer down." % host)

	# Update Tickets
	def updateTickets(self):
		logger.info("Refreshing DB.")
		for host in self.tickets.keys():
			# Put back in Q to refresh
			self.qin_toCheck.put(host)

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
	tmp = ('planetlab-1.cs.ucy.ac.cy','planetlab-2.vuse.vanderbilt.edu', 'planetlab-11.cs.princeton.edu', 'planet03.csc.ncsu.edu', 'planetlab1.pop-rj.rnp.br', 'planet1.halifax.canet4.nodes.planet-lab.org', 'planet1.cavite.nodes.planet-lab.org', 'ds-pl3.technion.ac.il', 'planetlab2.cs.purdue.edu', 'planetlab3.millennium.berkeley.edu', 'planetlab1.unl.edu', 'planetlab1.cs.colorado.edu', 'planetlab02.cs.washington.edu', 'orbpl2.rutgers.edu', 'planetlab2.informatik.uni-erlangen.de', 'pl2.ernet.in', 'neu2.6planetlab.edu.cn', 'planetlab-2.cs.uni-paderborn.de', 'planetlab1.elet.polimi.it', 'planetlab2.iiitb.ac.in', 'server1.planetlab.iit-tech.net', 'planetlab2.iitb.ac.in', 'planetlab1.ece.ucdavis.edu', 'planetlab02.dis.unina.it', 'planetlab-1.dis.uniroma1.it', 'planetlab1.iitb.ac.in', 'pku1.6planetlab.edu.cn', 'planetlab1.warsaw.rd.tp.pl', 'planetlab2.cs.unc.edu', 'csu2.6planetlab.edu.cn', 'pl1.ernet.in', 'planetlab2.georgetown.edu', 'planetlab1.cs.uchicago.edu') 
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
