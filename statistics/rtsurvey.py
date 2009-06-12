#!/usr/bin/python

import os, sys, shutil
import MySQLdb
import string

import re

import time 
from datetime import datetime

from monitor import config
from monitor import database

def convert_time(time_str):
	if '-' in str:
		try:
			tup = time.strptime(str, "%Y-%m-%d %H:%M:%S")
		except:
			tup = time.strptime(str, "%Y-%m-%d-%H:%M")
	elif '/' in str:
		tup = time.strptime(str, "%m/%d/%Y")
	else:
		tup = time.strptime(str, "%m/%d/%Y")
	d_ret = datetime.fromtimestamp(time.mktime(tup))
	return d_ret

def open_rt_db():

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
	

def get_rt_tickets():
	print "open db connection"
	db = open_rt_db()
	if db == -1:
		return ""

	sql = """SELECT tk.id, tk.Queue, tr.Type, tr.Field, tr.OldValue, tr.NewValue, 
                    tr.Created, at.id, at.Subject, at.Content
             FROM Tickets as tk, Transactions as tr 
             LEFT OUTER JOIN Attachments as at ON tr.id=at.TransactionId 
             WHERE (tk.Queue=3 OR tk.Queue=22) AND tk.id=tr.ObjectId AND tk.id>10000  """

	print "run query"
	raw = fetch_from_db(db, sql)
	if raw == -1:
		return raw
	
	tickets = {}
	subject_map = {}
	def parse_ticket(x):
		ticket_id = int(x[0])
		queue = int(x[1])
		trtype = str(x[2])
		field = x[3]
		oldvalue = x[4]
		newvalue = x[5]
		datecreated = x[6]		# already a datetime object
		attachmentid = x[7]
		subject = x[8]
		content = x[9]

		if ticket_id not in tickets:
			print "found new ticket_id", ticket_id
			tickets[ticket_id] = {'queue' : queue,
								  'transactions' : [] }

		if subject != "":
			subject_map[ticket_id] = subject
		elif ticket_id in subject_map:
			subject = subject_map[ticket_id]
		else:
			# subject == "" and no record in subject_map yet
			# should probably put on a queue to be processed later.
			print "no subject for %s" % ticket_id

		transaction = {
					'type' : trtype,
					'field' : field,
					'oldvalue' : oldvalue,
					'newvalue' : newvalue,
					'datecreated' : datecreated,
					'attachmentid' : attachmentid,
					'subject' : subject,
					'content' : content,
						}
		tickets[ticket_id]['transactions'].append(transaction)
		

	print "sort data"
	list = map(parse_ticket, raw)

	# map(lambda x: { "email":str(x[4]), "lastupdated":str(x[5]), "owner":str(x[7]), }, raw)

	db.close()


	return tickets


# flow chart:
#		classify:
#			for each ticket
#				classify into category
#				remove from ticket set, add to classified-set
#		
#		add new search patterns, 
#		re-run classify algorithm

re_map = [
	#('mom', {'pattern' : '.*pl_mom.*'}),
	#('technical-support', {'pattern' : '.*PlanetLab node.* down'}),
	#('technical-support', {'pattern' : 'Node .* was stopped by'}),  # and opened
	#('technical-support', {'pattern' : 'bootcd|BootCD|bootCD|boot cd|boot CD|booting'}),
	#('technical-support', {'pattern' : '.* failed to authenticate'}),
	#('technical-support', {'pattern' : '.* fails to boot'}),
	#('technical-support', {'pattern' : '.* fail.* to boot'}),
	#('technical-support', {'pattern' : '.* failed to authenticate'}),
	#('technical-support', {'pattern' : 'curl (60)|.* CA certificates.*|peer certificate.*authenticated'}),
	#('technical-support', {'pattern' : '(usb|USB).*(key|Disk|stick|boot|help|problem|trouble)'}), 
	#('complaint', {'pattern' : '.*omplaint|.*attack'}),
	#('complaint', {'pattern' : '.* stop .*'}), # and subject
	#('spam', {}),j
	#('user-support', {'pattern' : '(R|r)egistration|(R|r)egister'}),
	#('user-support', {'pattern' : 'password reset|reset password'}),
	('user-support', {'pattern' : 'New PI account registration from'}),
	#('other', {}),
]

def sort_tickets(tickets, re_map):

	ticket_count = len(tickets.keys())
	marked_subject = 0
	marked_content = 0
	for ticket_id in sorted(tickets.keys()):
		for i,(name, pattern) in enumerate(re_map):
			if 'compile' not in pattern:
				pattern['compile'] = re.compile(pattern['pattern'])
			pat = pattern['compile']
			for transaction in tickets[ticket_id]['transactions']:

				try:
					if transaction['subject'] and re.match(pat, transaction['subject']):
						print "ticket %s matches pattern %s: %s" % (ticket_id, 
								pattern['pattern'], transaction['subject'])
						marked_subject += 1
						break
					if transaction['content'] and re.match(pat, transaction['content']):
						print "ticket %s matches pattern %s: %s" % (ticket_id, 
								pattern['pattern'], transaction['subject'])
						#if transaction['subject'] == "":
						#	print transaction
						marked_content += 1
						break
				except:
					import traceback
					print traceback.print_exc()
					print transaction
					print ticket_id
					print pattern
					sys.exit(1)

	print ticket_count
	print marked_subject
	print marked_content
	print ticket_count - marked_content - marked_content

def main():
	from optparse import OptionParser
	parser = OptionParser()

	parser.set_defaults(runsql=False,)

	parser.add_option("", "--runsql", dest="runsql", action="store_true",
						help="Whether to collect data from the MySQL server before "+
							"caching it, or to just use the previously collected data.")

	(config, args) = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(1)

	for i,(name, pattern) in enumerate(re_map):
		print i, name

	if config.runsql:
		tickets = get_rt_tickets()
		database.dbDump("survey_tickets", tickets)
	else:
		print "loading"
		tickets = database.dbLoad("survey_tickets")
	print tickets[42171]['transactions'][0]

	sort_tickets(tickets, re_map)

	# for each ticket id
	#	scan for known keywords and sort into classes
	#	record assigned class

	# review all tickets that remain

if __name__ == '__main__':
	main()
