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

logger = logging.getLogger("monitor")

# Time to enforce policy
POLSLEEP = 7200

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
	def __init__(self, comonthread, tickets):
		self.cmn = comonthread
		self.tickets = tickets
		# host - > time of email
		self.emailed = {}
		# all sick nodes w/ tickets
		self.cursickw = tickets
		# all sick nodes w/o tickets
		self.cursick = []
		Thread.__init__(self)
	'''
	Gets all nodes without tickets and puts them in self.cursick
	'''
	def getAllSick(self):
		self.cursick = []
		for bucket in self.cmn.comonbkts.keys():
			for host in getattr(self.cmn, bucket):
				if host not in self.cursickw.keys():
					if host not in self.cursick: 
						self.cursick.append(host)
		logger.debug("Nodes sick wo tickets %s " % len(self.cursick))

	'''
	Acts on sick nodes.
	'''
	def emailSick(self):
		for node in self.cmn.ssh:
			if node in self.cursick:
				if node not in self.emailed.keys():
					logger.debug("Emailing " + node)
					try:
						self.emailed[node] = "ssh"
						mailer.email('DISREGARD', 
						emailTxt.mailtxt.STANDARD % {'hostname': node}, 
						"tech-" + mailer.siteId(node) + "@sites.planet-lab.org")
					except Exception, err:
						logger.info(err)

	'''
	Prints, logs, and emails status of up nodes, down nodes, and buckets.
	'''
	def status(self):
		return 0

	def run(self):
		#while 1:
		self.getAllSick()
		self.emailSick()
