#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $
#
# Policy Engine.

#from monitor import *
from threading import *
import time
import logging
import mailer
import emailTxt
import pickle
import xml, xmlrpclib
import Queue

DAT="./monitor.dat"

logger = logging.getLogger("monitor")

# Time to enforce policy
POLSLEEP = 7200

# Days between emails (enforce 'squeeze' after this time).
SQUEEZE = 3
# IF:
#  no SSH, down.
#  bad disk, down
#  DNS, kinda down (sick)
#  clock, kinda down (sick)
#  Full disk, going to be down

# Actions:
#  Email
#  suspend slice creation
#  kill slices
class Policy(Thread):
	def __init__(self, comonthread, sickNoTicket, emailed):
		self.cmn = comonthread
		# host - > (time of email, type of email)
		self.emailed = emailed 
		# all sick nodes w/o tickets
		self.sickNoTicket = sickNoTicket 
		Thread.__init__(self)
	
	#def getAllSick(self):
	#	for bucket in self.cmn.comonbkts.keys():
	#		for host in getattr(self.cmn, bucket):
	#			if host not in self.cursickw.keys():
	#				self.cursick.put(host)

	'''
	Acts on sick nodes
	'''
	def emailsick(self):
		# Get list of nodes in debug from PLC
		#dbgNodes = NodesDebug()

		node = self.sickNoTicket.get(block = True)
		# Get the login base	
		id = mailer.siteId(node)

		if not id: 
			logger.info("loginbase for %s not found" %node)
		elif node not in self.emailed.keys():
			# Email about Down.
			if node in self.cmn.down:
				logger.debug("POLICY: Emailing (down) " + node)
				self.emailed[node] = ("down", time.localtime())
				msg = emailTxt.mailtxt.DOWN \
					% {'hostname': node}
				mailer.email(node + " down", msg, 
				"tech-" + id + "@sites.planet-lab.org")
				return	

			# Email about no SSH.
			if node in self.cmn.ssh:
				logger.debug("POLICY: Emailing (ssh) " + node)
				self.emailed[node] = ("ssh", time.localtime())
				msg = emailTxt.mailtxt.SSH \
					% {'hostname': node}
				mailer.email(node + " down", msg, 
				"tech-" + id + "@sites.planet-lab.org")
				return 

			# Email about DNS
			if node in self.cmn.dns:
				logger.debug("POLICY: Emailing (dns)" + node)
				self.emailed[node] = ("dns", time.localtime())
				msg = emailTxt.mailtxt.DNS \
					% {'hostname': node}
				mailer.email("Please update DNS used by " \
				+ node, msg, 
				"tech-" + id + "@sites.planet-lab.org")
				return 
	

	'''
	Prints, logs, and emails status of up nodes, down nodes, and buckets.
	'''
	def status(self):
		return 0

	'''
	Store/Load state of emails.  When, where, what.
	'''
	def emailedStore(self, action):
		try:
			if action == "LOAD":
				f = open(DAT, "r+")
				logger.info("Found and reading " + DAT)
				self.emailed.update(pickle.load(f))
			if action == "WRITE":
				f = open(DAT, "w")
				logger.info("Writing " + DAT)
				pickle.dump(self.emailed, f)
			f.close()
		except Exception, err:
			logger.info("Problem with DAT, %s" %err)

	def run(self):
		while 1:
			self.emailsick()

'''
Returns list of nodes in dbg as reported by PLC
'''
def NodesDebug():
	dbgNodes = []
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	allnodes = api.AnonAdmGetNodes(anon, [], ['hostname','boot_state'])
	for node in allnodes:
		if node['boot_state'] == 'dbg': dbgNodes.append(node['hostname'])
	logger.info("%s nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes




def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	#print NodesDebug()
	tmp = Queue.Queue()
	a = Policy(None, tmp) 
	a.emailedStore("LOAD")
	print a.emailed

	os._exit(0)
if __name__ == '__main__':
	import os
	XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		os._exit(0)
