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

#Hack to auth structure
import auth 
DAT="./monitor.dat"

logger = logging.getLogger("monitor")

# Time to enforce policy
POLSLEEP = 7200

# Days between emails (enforce 'squeeze' after this time).
SQUEEZE = 3

# Where to email the summary
SUMTO = "faiyaza@cs.princeton.edu"
TECHEMAIL="tech-%s@sites.planet-lab.org"
PIEMAIL="pi-%s@sites.planet-lab.org"
SLICEMAIL="%s@slices.planet-lab.org"
PLCEMAIL="support@planet-lab.org"

#Thresholds
PITHRESH = 3
SLICETHRESH = 5

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
	def actOnSick(self):
		# Get list of nodes in debug from PLC
		#dbgNodes = NodesDebug()
		global TECHEMAIL, PIEMAIL
		node = self.sickNoTicket.get(block = True)
		# Get the login base	
		id = mailer.siteId(node)

 		# Send appropriate message for node if in appropriate bucket.
		# If we know where to send a message
		if not id: 
			logger.info("loginbase for %s not found" %node)
		# And we didn't email already.
		else:
			# If first email, send to Tech
			target = [TECHEMAIL % id]
			
			# If disk is foobarred, PLC should check it.
			if (node in self.cmn.filerw) and \
			(node not in self.emailed.keys()):
				target = [PLCEMAIL]	
				logger.info("Emailing PLC for " + node)

			# If in dbg, set to rins, then reboot.  Inform PLC.
			if (node in self.cmn.dbg):
				logger.info("Node in dbg - " + node)
				return

			# If its a disk, email PLC;  dont bother going through this loop.
			if (node in self.emailed.keys()) and \
			(node not in self.cmn.filerw):
				# If we emailed before, how long ago?	
				delta = time.localtime()[2] - self.emailed[node][1][2]
				# If more than PI thresh, but less than slicethresh
				if (delta >= PITHRESH) and (delta < SLICETHRESH): 
					logger.info("Emailing PI for " + node)
					target.append(PIEMAIL % id)
				# If more than PI thresh and slicethresh
				if (delta >= PITHRESH) and (delta > SLICETHRESH):
					logger.info("Emailing slices for " + node)
					# Email slices at site.
					slices = mailer.slices(id)
					if len(slices) >= 1:
						for slice in slices:
							target.append(SLICEMAIL % slice)

			# Find the bucket the node is in and send appropriate email
			# to approriate list of people.
			for bkt in self.cmn.comonbkts.keys():
				if (node in getattr(self.cmn, bkt)):
					# Send predefined message for that bucket.
					logger.info("POLICY: Emailing (%s) %s - %s"\
						%(bkt, node, target))
					tmp = getattr(emailTxt.mailtxt, bkt)
					sbj = tmp[0] % {'hostname': node}
					msg = tmp[1] % {'hostname': node}
					mailer.email(sbj, msg, target)	
					self.emailed[node] = (bkt , time.localtime())
					return


	'''
	Prints, logs, and emails status of up nodes, down nodes, and buckets.
	'''
	def status(self):
		sub = "Monitor Summary"
		msg = "\nThe following nodes were acted upon:  \n\n"
		for (node, (type, date)) in self.emailed.items():
			msg +="%s\t(%s)\t%s:%s:%s\n" %(node,type,date[3],date[4],date[5])
		mailer.email(sub, msg, [SUMTO])
		logger.info(msg)
		return 

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
				logger.debug("Writing " + DAT)
				pickle.dump(self.emailed, f)
			f.close()
		except Exception, err:
			logger.info("Problem with DAT, %s" %err)

	def run(self):
		while 1:
			self.actOnSick()
			self.emailedStore("WRITE")
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
	#tmp = Queue.Queue()
	#a = Policy(None, tmp) 
	#a.emailedStore("LOAD")
	#print a.emailed
	print siteId("princetoan")

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
