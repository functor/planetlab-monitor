#!/usr/bin/python

# This script is used to manipulate the operational state of nodes in
# different node groups.  These are basically set operations on nodes via the
# PLC api.
# 
# Take the ng name as an argument....
# optionally, 
#  * get a list of nodes in the given nodegroup.
#  * set some or all in the set to rins.
#  * restart them all.
#  * do something else to them all.
# 

import os
import time
import traceback
import sys
from optparse import OptionParser

import bootman 		# debug nodes

from monitor import util
from monitor import const
from monitor import reboot
from monitor import config
from monitor import database
from monitor import parser as parsermodule
from monitor.common import *
from monitor.model import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.wrapper.emailTxt import mailtxt
from monitor.database.info.model import *

from nodequery import verify,query_to_dict,node_select

api = plc.getAuthAPI()


class SiteInterface(HistorySiteRecord):
	@classmethod
	def get_or_make(cls, if_new_set={}, **kwargs):
		if 'hostname' in kwargs:
			kwargs['loginbase'] = plccache.plcdb_hn2lb[kwargs['hostname']]
			del kwargs['hostname']
		res = HistorySiteRecord.findby_or_create(if_new_set, **kwargs)
		return SiteInterface(res)
	
	def __init__(self, sitehist):
		self.db = sitehist

	def getRecentActions(self, **kwargs):
		# TODO: make query only return records within a certin time range,
		# i.e. greater than 0.5 days ago. or 5 days, etc.

		#print "kwargs: ", kwargs

		recent_actions = []
		if 'loginbase' in kwargs:
			recent_actions = ActionRecord.query.filter_by(loginbase=kwargs['loginbase']).order_by(ActionRecord.date_created.desc())
		elif 'hostname' in kwargs:
			recent_actions = ActionRecord.query.filter_by(hostname=kwargs['hostname']).order_by(ActionRecord.date_created.desc())
		return recent_actions
	
	def increasePenalty(self):
		#act = ActionRecord(loginbase=self.db.loginbase, action='penalty', action_type='increase_penalty',)
		self.db.penalty_level += 1
		# NOTE: this is to prevent overflow or index errors in applyPenalty.
		#       there's probably a better approach to this.
		if self.db.penalty_level >= 2:
			self.db.penalty_level = 2
		self.db.penalty_applied = True
	
	def applyPenalty(self):
		penalty_map = [] 
		penalty_map.append( { 'name': 'noop',      		'enable'   : lambda site: None,
														'disable'  : lambda site: None } )
		penalty_map.append( { 'name': 'nocreate',		'enable'   : lambda site: plc.removeSiteSliceCreation(site),
														'disable'  : lambda site: plc.enableSiteSliceCreation(site) } )
		penalty_map.append( { 'name': 'suspendslices',	'enable'   : lambda site: plc.suspendSiteSlices(site),
														'disable'  : lambda site: plc.enableSiteSlices(site) } )

		for i in range(len(penalty_map)-1,self.db.penalty_level,-1):
			print "\tdisabling %s on %s" % (penalty_map[i]['name'], self.db.loginbase)
			penalty_map[i]['disable'](self.db.loginbase) 

		for i in range(0,self.db.penalty_level+1):
			print "\tapplying %s on %s" % (penalty_map[i]['name'], self.db.loginbase)
			penalty_map[i]['enable'](self.db.loginbase)

		return

	def pausePenalty(self):
		act = ActionRecord(loginbase=self.db.loginbase,
							action='penalty',
							action_type='pause_penalty',)
	
	def clearPenalty(self):
		#act = ActionRecord(loginbase=self.db.loginbase, action='penalty', action_type='clear_penalty',)
		self.db.penalty_level = 0
		self.db.penalty_applied = False
	
	def getTicketStatus(self):
		if self.db.message_id != 0:
			rtstatus = mailer.getTicketStatus(self.db.message_id)
			self.db.message_status = rtstatus['Status']
			self.db.message_queue = rtstatus['Queue']
			self.db.message_created = datetime.fromtimestamp(rtstatus['Created'])

	def setTicketStatus(self, status):
		print 'SETTING status %s' % status
		if self.db.message_id != 0:
			rtstatus = mailer.setTicketStatus(self.db.message_id, status)

	def getContacts(self):
		contacts = []
		if self.db.penalty_level >= 0:
			contacts += plc.getTechEmails(self.db.loginbase)

		if self.db.penalty_level >= 1:
			contacts += plc.getPIEmails(self.db.loginbase)

		if self.db.penalty_level >= 2:
			contacts += plc.getSliceUserEmails(self.db.loginbase)

		return contacts

	def sendMessage(self, type, **kwargs):

		# NOTE: evidently changing an RT message's subject opens the ticket.
		#       the logic in this policy depends up a ticket only being 'open'
        #       if a user has replied to it.
        #       So, to preserve these semantics, we check the status before
        #           sending, then after sending, reset the status to the
        #           previous status.
        #       There is a very tiny race here, where a user sends a reply
        #           within the time it takes to check, send, and reset.
        #       This sucks.  It's almost certainly fragile.

		# 
		# TODO: catch any errors here, and add an ActionRecord that contains
		#       those errors.
		
		args = {'loginbase' : self.db.loginbase, 'penalty_level' : self.db.penalty_level}
		args.update(kwargs)

		hostname = None
		if 'hostname' in args:
			hostname = args['hostname']

		if hasattr(mailtxt, type):

			message = getattr(mailtxt, type)
			viart = True
			if 'viart' in kwargs:
				viart = kwargs['viart']

			if viart:
				self.getTicketStatus()		# get current message status

			m = Message(message[0] % args, message[1] % args, viart, self.db.message_id)

			contacts = self.getContacts()
			contacts = [config.cc_email]	# TODO: remove after testing...

			print "sending message: %s to site %s for host %s" % (type, self.db.loginbase, hostname)

			ret = m.send(contacts)
			if viart:
				self.db.message_id = ret
				# reset to previous status, since a new subject 'opens' RT tickets.
				self.setTicketStatus(self.db.message_status) 

				# NOTE: only make a record of it if it's in RT.
				act = ActionRecord(loginbase=self.db.loginbase, hostname=hostname, action='notice', 
								action_type=type, message_id=self.db.message_id)

		else:
			print "+-- WARNING! ------------------------------"
			print "| No such message name in emailTxt.mailtxt: %s" % type
			print "+------------------------------------------"

		return

	def closeTicket(self):
		# TODO: close the rt ticket before overwriting the message_id
		mailer.closeTicketViaRT(self.db.message_id, "Ticket Closed by Monitor")
		act = ActionRecord(loginbase=self.db.loginbase, action='notice', 
							action_type='end_notice', message_id=self.db.message_id)
		self.db.message_id = 0
		self.db.message_status = "new"

	def runBootManager(self, hostname):
		print "attempting BM reboot of %s" % hostname
		ret = ""
		try:
			ret = bootman.restore(self, hostname)
			err = ""
		except:
			err = traceback.format_exc()
			print err

		act = ActionRecord(loginbase=self.db.loginbase,
							hostname=hostname,
							action='reboot',
							action_type='bootmanager_restore',
							error_string=err)
		return ret

	def attemptReboot(self, hostname):
		print "attempting PCU reboot of %s" % hostname
		ret = reboot.reboot_str(hostname)
		if ret == 0 or ret == "0":
			ret = ""
		act = ActionRecord(loginbase=self.db.loginbase,
							hostname=hostname,
							action='reboot',
							action_type='first_try_reboot',
							error_string=ret)

def logic():

	plc.nodeBootState(host, 'rins')
	node_end_record(host)




def main(hostnames, sitenames):
	# commands:
	i = 1
	node_count = 1
	site_count = 1
	#print "hosts: %s" % hostnames
	for host in hostnames:
		try:
			lb = plccache.plcdb_hn2lb[host]
		except:
			print "unknown host in plcdb_hn2lb %s" % host
			continue

		nodeblack = BlacklistRecord.get_by(hostname=host)

		if nodeblack and not nodeblack.expired():
			print "skipping %s due to blacklist.  will expire %s" % (host, nodeblack.willExpire() )
			continue

		sitehist = SiteInterface.get_or_make(loginbase=lb)

		recent_actions = sitehist.getRecentActions(hostname=host)

		nodehist = HistoryNodeRecord.findby_or_create(hostname=host)

		print "%s %s" % ( nodehist.hostname, nodehist.status)
		if nodehist.status == 'good' and \
			changed_lessthan(nodehist.last_changed, 1.0) and \
			not found_within(recent_actions, 'online_notice', 0.5):
				# NOTE: there is a narrow window in which this command must be
				# evaluated, otherwise the notice will not go out.  this is not ideal.
				sitehist.sendMessage('online_notice', hostname=host)
				print "send message for host %s online" % host

				pass

		if ( nodehist.status == 'offline' or nodehist.status == 'down' ) and \
			changed_greaterthan(nodehist.last_changed,1.0) and \
			not found_between(recent_actions, 'first_try_reboot', 3.5, 1):

				sitehist.attemptReboot(host)
				print "send message for host %s first_try_reboot" % host
				pass

		# NOTE: non-intuitive is that found_between(first_try_reboot, 3.5, 1)
		# 		will be false for a day after the above condition is satisfied
		if ( nodehist.status == 'offline' or nodehist.status == 'down' ) and \
			changed_greaterthan(nodehist.last_changed,1.5) and \
			found_between(recent_actions, 'first_try_reboot', 3.5, 1) and \
			not found_within(recent_actions, 'pcufailed_notice', 3.5):
			# found_within(recent_actions, 'first_try_reboot', 3.5) and \
				
				# send pcu failure message
				#act = ActionRecord(**kwargs)
				sitehist.sendMessage('pcufailed_notice', hostname=host)
				print "send message for host %s PCU Failure" % host
				pass

		if nodehist.status == 'monitordebug' and \
			changed_greaterthan(nodehist.last_changed, 1) and \
			not found_between(recent_actions, 'bootmanager_restore', 0.5, 0):
				# send down node notice
				# delay 0.5 days before retrying...

				print "send message for host %s bootmanager_restore" % host
				sitehist.runBootManager(host)
			#	sitehist.sendMessage('retry_bootman', hostname=host)

		if nodehist.status == 'down' and \
			changed_greaterthan(nodehist.last_changed, 2) and \
			not found_within(recent_actions, 'down_notice', 3.5):
				# send down node notice

				sitehist.sendMessage('down_notice', hostname=host)
				print "send message for host %s offline" % host
				pass

		node_count = node_count + 1

	for site in sitenames:
		sitehist = SiteInterface.get_or_make(loginbase=site)
		# TODO: make query only return records within a certin time range,
		# 		i.e. greater than 0.5 days ago. or 5 days, etc.
		recent_actions = sitehist.getRecentActions(loginbase=site)

		#sitehist.sendMessage('test_notice', host)

		print "%s %s" % ( sitehist.db.loginbase , sitehist.db.status)
		if sitehist.db.status == 'down':
			if  not found_within(recent_actions, 'pause_penalty', 30) and \
				not found_within(recent_actions, 'increase_penalty', 7) and \
				changed_greaterthan(sitehist.db.last_changed, 7):

				# TODO: catch errors
				sitehist.increasePenalty()
				#sitehist.applyPenalty()
				sitehist.sendMessage('increase_penalty')

				print "send message for site %s penalty increase" % site

		if sitehist.db.status == 'good':
			# clear penalty
			# NOTE: because 'all clear' should have an indefinite status, we
			# 		have a boolean value rather than a 'recent action'
			if sitehist.db.penalty_applied:
				# send message that penalties are cleared.

				sitehist.clearPenalty()
				#sitehist.applyPenalty()
				sitehist.sendMessage('clear_penalty')
				sitehist.closeTicket()

				print "send message for site %s penalty cleared" % site

		# find all ticket ids for site ( could be on the site record? )
		# determine if there are penalties within the last 30 days?
		# if so, add a 'pause_penalty' action.
		if sitehist.db.message_id != 0 and sitehist.db.message_status == 'open' and sitehist.db.penalty_level > 0:
			#	pause escalation
			print "Pausing penalties for %s" % site
			sitehist.pausePenalty()

		site_count = site_count + 1

	session.flush()

	return


if __name__ == "__main__":
	parser = parsermodule.getParser(['nodesets'])
	parser.set_defaults( timewait=0,
						skip=0,
						rins=False,
						reboot=False,
						findbad=False,
						force=False, 
						nosetup=False, 
						verbose=False, 
						quiet=False,
						)

	parser.add_option("", "--stopselect", dest="stopselect", metavar="", 
						help="The select string that must evaluate to true for the node to be considered 'done'")
	parser.add_option("", "--findbad", dest="findbad", action="store_true", 
						help="Re-run findbad on the nodes we're going to check before acting.")
	parser.add_option("", "--force", dest="force", action="store_true", 
						help="Force action regardless of previous actions/logs.")
	parser.add_option("", "--rins", dest="rins", action="store_true", 
						help="Set the boot_state to 'rins' for all nodes.")
	parser.add_option("", "--reboot", dest="reboot", action="store_true", 
						help="Actively try to reboot the nodes, keeping a log of actions.")

	parser.add_option("", "--verbose", dest="verbose", action="store_true", 
						help="Extra debug output messages.")
	parser.add_option("", "--nosetup", dest="nosetup", action="store_true", 
						help="Do not perform the orginary setup phase.")
	parser.add_option("", "--skip", dest="skip", 
						help="Number of machines to skip on the input queue.")
	parser.add_option("", "--timewait", dest="timewait", 
						help="Minutes to wait between iterations of 10 nodes.")

	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

#	# COLLECT nodegroups, nodes and node lists
#	if config.nodegroup:
#		ng = api.GetNodeGroups({'name' : config.nodegroup})
#		nodelist = api.GetNodes(ng[0]['node_ids'])
#		hostnames = [ n['hostname'] for n in nodelist ]

	fbquery = HistoryNodeRecord.query.all()
	hostnames = [ n.hostname for n in fbquery ]
	
	fbquery = HistorySiteRecord.query.all()
	sitenames = [ s.loginbase for s in fbquery ]

	if config.site:
		# TODO: replace with calls to local db.  the api fails so often that
		# 		these calls should be regarded as unreliable.
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['hostname'])
		filter_hostnames = [ n['hostname'] for n in l_nodes ]

		hostnames = filter(lambda x: x in filter_hostnames, hostnames)
		sitenames = [config.site]

	if config.node:
		hostnames = [ config.node ] 
		sitenames = [ plccache.plcdb_hn2lb[config.node] ]

	try:
		main(hostnames, sitenames)
	except KeyboardInterrupt:
		print "Killed by interrupt"
		sys.exit(0)
	except:
		#email_exception()
		print traceback.print_exc();
		print "Continuing..."
