#!/usr/bin/python2

import os, sys, shutil
import MySQLdb
import string
import logging
import Queue
import time 
import re
from threading import *

from monitor import config
from monitor import database

# TODO: merge the RT mailer from mailer.py into this file.

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
	#rt_db_constants= readConstantsFile(RT_DB_CONSTANTS_PATH)
	#if rt_db_constants is None:
	#	print "Unable to read database access constants from %s" % \
	#		  RT_DB_CONSTANTS_PATH
	#	return -1

	try:
		rt_db = MySQLdb.connect(host=config.RT_DB_HOST,
								user=config.RT_DB_USER,
		   						passwd=config.RT_DB_PASSWORD,
								db=config.RT_DB_NAME)
	except Exception, err:
		print "Failed to connect to RT database: %s" %err
		return -1

	return rt_db



def fetch_from_db(db, sql):
	try:
		# create a 'cursor' (required by MySQLdb)
		c = db.cursor()
		c.execute(sql)
	except Exception, err:
		print "Could not execute RT query %s" %err
		return -1

	# fetch all rows (list of lists)
	raw = c.fetchall()
	return raw
	

def rt_tickets():
	db = open_rt_db()
	if db == -1:
		return ""
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
# SELECT Tk.* FROM Tickets AS Tk, Attachments AS At JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId  WHERE Tk.Queue != 10 AND Tk.id > 10000 AND Tr.id=At.TransactionID AND Tk.Status = 'open' ;
# 

	sql = """SELECT distinct Tk.id, Tk.Status, Tk.Subject, At.Content
			 FROM Tickets AS Tk, Attachments AS At 
			 JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId  
			 WHERE Tk.Queue != 10 AND Tk.id > 10000 AND 
			 	   Tr.id=At.TransactionID AND Tk.Status = 'open'"""
			 	   #Tr.id=At.TransactionID AND (Tk.Status = 'new' OR Tk.Status = 'open')"""
	#sqlall = """SELECT distinct Tk.id, Tk.Status, Tk.Subject, At.Content
#FROM Tickets AS Tk, Attachments AS At 
#JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId  
#WHERE Tk.Queue != 10 AND Tk.id > 10000 AND 
#Tr.id=At.TransactionID AND ( Tk.Status = 'open' OR
#Tk.Status = 'new') """
	sqlall = """SELECT distinct Tk.id, Tk.Status, Tk.Subject, At.Content, Us.EmailAddress, Tk.LastUpdated, Q.Name, Tk.Owner FROM Tickets AS Tk, Attachments AS At, Queues as Q, Users as Us JOIN Transactions AS Tr ON Tk.id=Tr.ObjectId WHERE (Tk.Queue=3 OR Tk.Queue=22) AND Tk.id > 10000 AND Tr.id=At.TransactionID AND ( Tk.Status = 'open' OR Tk.Status = 'new') AND Us.id=Tk.LastUpdatedBy AND Q.id=Tk.Queue """


	raw = fetch_from_db(db, sql)
	if raw == -1:
		return raw
	tickets = map(lambda x: {"ticket_id":str(x[0]),
				"status":x[1],
				"subj":str(x[2]),
				"content":str(x[3])},
				raw)

	raw = fetch_from_db(db,sqlall)
	if raw == -1:
		return raw
	tickets_all = map(lambda x: {"ticket_id":str(x[0]),
				"status":x[1],
				"subj":str(x[2]),
				"content":str(x[3]),
				"email":str(x[4]),
				"lastupdated":str(x[5]),
				"queue":str(x[6]),
				"owner":str(x[7]),
				},
				raw)

	db.close()

	idTickets = {}
	for t in tickets_all:
		idTickets[t['ticket_id']] = t
	database.dbDump("idTickets", idTickets)

	return tickets

def is_host_in_rt_tickets(host, ticket_blacklist, ad_rt_tickets):
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
				logger.debug("\t ticket %s has %s" % (x['ticket_id'], host))
				print "\t ticket %s has %s" % (x['ticket_id'], host)
				if x['ticket_id'] in ticket_blacklist:
					return (False, x)
				else:
					return (True, x)
		print "\t noticket -- has %s" % host
		#logger.debug("\t noticket -- has %s" % host)
		return (False, None)

	# This search, while O(tickets), takes less than a millisecond, 05-25-07
	#t = commands.MyTimer()
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
	def __init__(self, dbTickets, q_toRT, q_fromRT, l_ticket_blacklist, target = None): 
		# Time of last update of ticket DB
		self.dbTickets = dbTickets
		self.lastupdated = 0
		self.l_ticket_blacklist = l_ticket_blacklist
		self.q_toRT = q_toRT
		self.q_fromRT = q_fromRT 
		self.tickets = {}
		Thread.__init__(self,target = self.getTickets)

	# Takes node from q_toRT, gets tickets.  
	# Thread that actually gets the tickets.
	def getTickets(self):
		self.count = 0
		while 1:
			diag_node = self.q_toRT.get(block = True)
			if diag_node != None: 
				host = diag_node['nodename']
				(b_host_inticket, r_ticket) = is_host_in_rt_tickets(host, \
													self.l_ticket_blacklist, \
													self.dbTickets)
				diag_node['found_rt_ticket'] = None
				if b_host_inticket:
					logger.debug("RT: found tickets for %s" %host)
					diag_node['found_rt_ticket'] = r_ticket['ticket_id']

				else:
					if r_ticket is not None:
						print "Ignoring ticket %s" % r_ticket['ticket_id']
						# TODO: why do i return the ticket id for a
						# 		blacklisted ticket id?
						#diag_node['found_rt_ticket'] = r_ticket['ticket_id']
					self.count = self.count + 1

				self.q_fromRT.put(diag_node) 
			else:
				print "RT processed %d nodes with noticket" % self.count
				logger.debug("RT filtered %d noticket nodes" % self.count)
				self.q_fromRT.put(None)

				break

	# Removes hosts that are no longer down.
	def remTickets(self):
		logger.debug("Removing stale entries from DB.") 
		prevdown = self.tickets.keys()

		currdown = []
		##BEGIN HACK.  This should be outside of this file. passed to class.
		#cmn = comon.Comon(None, None)
        #	cmn.updatebkts()
		#for bucket in cmn.comonbkts.keys():
		#	for host in getattr(cmn,bucket):
		#		if host not in currdown: currdown.append(host)
		##END HACK

		# Actually do the comparison
		#for host in prevdown:
		#	if host not in currdown:
		#		del self.tickets[host]
		#		logger.info("RT: %s no longer down." % host)

	# Update Tickets
	def updateTickets(self):
		logger.info("Refreshing DB.")
		for host in self.tickets.keys():
			# Put back in Q to refresh
			self.q_toRT.put(host)

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

	tickets = rt_tickets()
	database.dbDump("ad_dbTickets", tickets)


if __name__ == '__main__':
    main()
