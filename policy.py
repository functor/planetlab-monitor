#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: policy.py,v 1.12 2007/04/06 17:38:14 faiyaza Exp $
#
# Policy Engine.

#from monitor import *
from threading import *
import time
import logging
import mailer
import emailTxt
import pickle
import Queue
import plc
import reboot
import config

DAT="./monitor.dat"

logger = logging.getLogger("monitor")

# Time to enforce policy
POLSLEEP = 7200

# Where to email the summary
SUMTO = "faiyaza@cs.princeton.edu"
TECHEMAIL="tech-%s@sites.planet-lab.org"
PIEMAIL="pi-%s@sites.planet-lab.org"
SLICEMAIL="%s@slices.planet-lab.org"
PLCEMAIL="support@planet-lab.org"

#Thresholds (DAYS)
SPERDAY = 86400
PITHRESH = 7 * SPERDAY
SLICETHRESH = 7 * SPERDAY
# Days before attempting rins again
RINSTHRESH = 5 * SPERDAY

# Days before calling the node dead.
DEADTHRESH = 30 * SPERDAY
# Minimum number of nodes up before squeezing
MINUP = 2

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
		# from thread 
		self.sickNoTicket = sickNoTicket
		# Actions taken on nodes.
		# actionlogdb{node: [action, date]} 
		self.actionlogdb = {}
		# Actions taken on sites.
		# sitelogdb{site: [action, daysdown, date]} 
		self.sitelogdb = {}
		# sick nodes with no tickets 
		# sickdb{loginbase: [{hostname1: [buckets]}, {...}]}
		self.sickdb = {}
		Thread.__init__(self)


	def accumSickSites(self):
		"""
		Take all sick nodes, find their sites, and put in 
		sickdb{loginbase: [{hostname1: [buckets]}, {...}]}
		"""
		while self.sickNoTicket.empty() == False:
			node = self.sickNoTicket.get(block = True)
			bkts= []
			for bkt in self.cmn.comonbkts.keys():
				if (node in getattr(self.cmn, bkt)):
					bkts.append("%s" % bkt)
			self.sickdb[plc.siteId(node)] = {node: bkts}


	def __actOnDebug(self, node):
		"""
		If in debug, set the node to rins, reboot via PCU/POD
		"""
		daysdown = self.cmn.codata[node]['sshstatus'] // (60*60*24)
		logger.info("POLICY:  Node %s in dbg.  down for %s" %(node,daysdown))
		plc.nodeBootState(node, "rins")	
		# If it has a PCU
		reboot.reboot(node)
		# Log it 
		self.actionlogdb[node] = ['rins', daysdown, time.time()] 


	def __actOnDown(self, node):
		"""
		If down (not debug), do the same as actOnDebug for now
		"""
		self.__actOnDebug(node)	


	def __actOnFilerw(self, node):
		"""
		Report to PLC when node needs disk checked.	
		"""
		target = [PLCEMAIL]	
		logger.info("POLICY:  Emailing PLC for " + node)
		tmp = emailTxt.mailtxt.filerw
		sbj = tmp[0] % {'hostname': node}
		msg = tmp[1] % {'hostname': node}
		mailer.email(sbj, msg, target)	
		self.actionlogdb[node] = ["filerw", None, time.time()]


	def __actOnDNS(self, node):
		"""
		"""


	def __policy(self, node, loginbase, bkt):
		# ...and spam 'em
		target = [TECHEMAIL % loginbase]
		tmp = emailTxt.mailtxt.down
		sbj = tmp[0] % {'hostname': node}
		msg = tmp[1] % {'hostname': node, 'days': daysdown}
		mailer.email(sbj, msg, target)	




	def actOnSick(self):
		"""
		Acts on sick nodes.
		"""
		global TECHEMAIL, PIEMAIL
		
		# Princeton Backdoor
		if loginbase == "princeton": return

		# Send appropriate message for node if in appropriate bucket.
		# If we know where to send a message
		if not loginbase: 
			logger.info("POLICY:  loginbase for %s not found" %node)
		# And we didn't email already.
		else:
			# If first email, send to Tech
			target = [TECHEMAIL % loginbase]
			
			# If disk is foobarred, PLC should check it.
			if (node in self.cmn.filerw) and \
			(node not in self.emailed.keys()):
				self.__actOnFilerw(node)
				return 

			# If in dbg, set to rins, then reboot.  Inform PLC.
			if (node in self.cmn.dbg):
				self.__actOnDebug(node)

			if (node in self.emailed.keys()) and \
			(node not in self.cmn.filerw)    and \
			(node not in self.cmn.clock_drift):
				# If we emailed before, how long ago?	
				delta = time.time() - self.emailed[node][1]
				if delta < SPERDAY:  
					logger.info("POLICY:  already acted on %s today." % node)
					return

				logger.info("POLICY:  acted %s on %s days ago" % (node, 
				delta // SPERDAY))
			
				# If no luck with tech, email PI
				if (delta >= SPERDAY):
					target.append(PIEMAIL % loginbase)

				if (delta >= 7 * SPERDAY): 
					#remove slice creation if enough nodes arent up
					if not self.enoughUp(loginbase):
						slices = plc.slices(loginbase)
						if len(slices) >= 1:
							for slice in slices:
								target.append(SLICEMAIL % slice)
						logger.info("POLICY:  Removing slice creation from %s" % loginbase)
						tmp = emailTxt.mailtxt.removedSliceCreation
						sbj = tmp[0] 
						msg = tmp[1] % {'loginbase': loginbase}
						plc.removeSliceCreation(node)
						mailer.email(sbj, msg, target)	
						self.squeezed[loginbase] = (time.time(), "creation")
						self.emailed[node] = ("creation", time.time())	
						logger.info("POLICY: Emailing (%s) %s - %s"\
							%("creation", node, target))
						return

				if (delta >= 14 * SPERDAY):
					target.append(PIEMAIL % loginbase)
					# Email slices at site.
					slices = plc.slices([loginbase])
					if len(slices) >= 1:
						for slice in slices:
							target.append(SLICEMAIL % slice)
					# If not enough up, freeze slices and email everyone.
					if not self.enoughUp(loginbase):
						logger.info("POLICY:  Suspending %s slices." % loginbase)
						tmp = emailTxt.mailtxt.suspendSlices
						sbj = tmp[0] 
						msg = tmp[1] % {'loginbase': loginbase}
						plc.suspendSlices([node])
						self.squeezed[loginbase] = (time.time(), "freeze")
						mailer.email(sbj, msg, target)	
						self.emailed[node] = ("freeze", time.time())
						logger.info("POLICY: Emailing (%s) %s - %s"\
							%("freeze", node, target))

						return

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
					self.emailed[node] = (bkt , time.time())
					return


	"""
	Prints, logs, and emails status of up nodes, down nodes, and buckets.
	"""
	def status(self):
		sub = "Monitor Summary"
		msg = "\nThe following nodes were acted upon:  \n\n"
		for (node, (type, date)) in self.emailed.items():
			# Print only things acted on today.
			if (time.gmtime(time.time())[2] == time.gmtime(date)[2]):
				msg +="%s\t(%s)\t%s\n" %(node, type, time.ctime(date))
		msg +="\n\nThe following sites have been 'squeezed':\n\n"
		for (loginbase, (date, type)) in self.squeezed.items():
			# Print only things acted on today.
			if (time.gmtime(time.time())[2] == time.gmtime(date)[2]):
				msg +="%s\t(%s)\t%s\n" %(loginbase, type, time.ctime(date))
		mailer.email(sub, msg, [SUMTO])
		logger.info(msg)
		return 

	"""
	Store/Load state of emails.  When, where, what.
	"""
	def emailedStore(self, action):
		try:
			if action == "LOAD":
				f = open(DAT, "r+")
				logger.info("POLICY:  Found and reading " + DAT)
				self.emailed.update(pickle.load(f))
			if action == "WRITE":
				f = open(DAT, "w")
				#logger.debug("Writing " + DAT)
				pickle.dump(self.emailed, f)
			f.close()
		except Exception, err:
			logger.info("POLICY:  Problem with DAT, %s" %err)

	"""
	Returns True if more than MINUP nodes are up at a site.
	"""
	def enoughUp(self, loginbase):
		allsitenodes = plc.getSiteNodes([loginbase])
		if len(allsitenodes) == 0:
			logger.info("Node not in db")
			return

		numnodes = len(allsitenodes)
		sicknodes = []
		# Get all sick nodes from comon
		for bucket in self.cmn.comonbkts.keys():
			for host in getattr(self.cmn, bucket):
				sicknodes.append(host)
		# Diff.
		for node in allsitenodes:
			if node in sicknodes:
				numnodes -= 1

		if numnodes < MINUP:
			logger.info(\
"POLICY:  site with %s has nodes %s up." %(loginbase, numnodes))
			return False 
		else: 
			return True 
			
		


	def run(self):
		self.accumSickSites()
		#self.actOnSick()
		#self.emailedStore("WRITE")
		print self.sickdb
	


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

	#print plc.slices([plc.siteId(["alice.cs.princeton.edu"])])
	os._exit(0)
if __name__ == '__main__':
	import os
	import plc
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		os._exit(0)
