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

from monitor import config
from monitor import parser as parsermodule
from monitor.common import *
from monitor.const import MINUP
from monitor.model import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.database.info.model import *
from monitor.database.info.interface import *

from monitor.query import verify,query_to_dict,node_select

api = plc.getAuthAPI()

def logic():

	plc.nodeBootState(host, 'reinstall')
	node_end_record(host)

def check_node_and_pcu_status_for(loginbase):
	"""
		this function checks whether all the nodes and associated pcus for a
		given site are considered 'good'.  
		
		If so, the function returns True.
		Otherwise, the function returns False.
	"""

	results = [] 
	for node in plccache.plcdb_lb2hn[loginbase]:

		noderec  = FindbadNodeRecord.findby_or_create(hostname=node['hostname'])
		nodehist = HistoryNodeRecord.findby_or_create(hostname=node['hostname'])
		nodebl   = BlacklistRecord.get_by(hostname=node['hostname'])
		pcuhist  = HistoryPCURecord.get_by(plc_pcuid=noderec.plc_pcuid)

		if (nodehist is not None and nodehist.status == 'good' and \
			((pcuhist is not None and pcuhist.status == 'good') or (pcuhist is None)) ):
			if nodebl is None: 			# no entry in blacklist table
				results.append(True)
			elif nodebl is not None and nodebl.expired():	# expired entry in blacklist table
				results.append(True)
			else:
				results.append(False)	# entry that is not expired.
		else:
			results.append(False)

	try:
		print "test: %s" % results
		# NOTE: incase results is empty, reduce does not work on an empty set.
		return reduce(lambda x,y: x&y, results) and len(results) > MINUP
	except:
		return False

def main(hostnames, sitenames):
	# commands:
	i = 1
	node_count = 1
	site_count = 1
	#print "hosts: %s" % hostnames
	print "apply-policy"
	for i,host in enumerate(hostnames):
		try:
			lb = plccache.plcdb_hn2lb[host]
		except:
			print "unknown host in plcdb_hn2lb %s" % host
			email_exception("%s %s" % (i,host))
			continue

		nodeblack = BlacklistRecord.get_by(hostname=host)

		if nodeblack and not nodeblack.expired():
			print "skipping %s due to blacklist.  will expire %s" % (host, nodeblack.willExpire() )
			continue

		sitehist = SiteInterface.get_or_make(loginbase=lb)

		recent_actions = sitehist.getRecentActions(hostname=host)

		nodehist = HistoryNodeRecord.findby_or_create(hostname=host)

		print "%s %s %s" % (i, nodehist.hostname, nodehist.status)
		if nodehist.status == 'good' and \
			changed_lessthan(nodehist.last_changed, 1.0) and \
			found_within(recent_actions, 'down_notice', 7.0) and \
			not found_within(recent_actions, 'online_notice', 0.5):
				# NOTE: chronicly flapping nodes will not get 'online' notices
				# 		since, they are never up long enough to be 'good'.
				# NOTE: searching for down_notice proves that the node has
				# 		gone through a 'down' state first, rather than just
				# 		flapping through: good, offline, online, ...
				# 	
				# NOTE: there is a narrow window in which this command must be
				# 		evaluated, otherwise the notice will not go out.  
				#		this is not ideal.
				sitehist.sendMessage('online_notice', hostname=host, viart=False, saveact=True)
				print "send message for host %s online" % host


		# if a node is offline and doesn't have a PCU, remind the user that they should have one.
		#if not nodehist.haspcu and nodehist.status in ['offline', 'down'] and \
		#	changed_greaterthan(nodehist.last_changed,1.0) and \
		#	not found_within(recent_actions, 'pcumissing_notice', 7.0):
		#
		#		sitehist.sendMessage('pcumissing_notice', hostname=host)
		#		print "send message for host %s pcumissing_notice" % host

		# if it is offline and HAS a PCU, then try to use it.
		if nodehist.haspcu and nodehist.status in ['offline', 'down'] and \
			changed_greaterthan(nodehist.last_changed,1.0) and \
			not nodehist.firewall and \
			not found_between(recent_actions, 'try_reboot', 3.5, 1):

				# TODO: there MUST be a better way to do this... 
				# get fb node record for pcuid
				fbpcu = None
				fbnode = FindbadNodeRecord.get_latest_by(hostname=host)
				if fbnode:
					fbpcu = FindbadPCURecord.get_latest_by(plc_pcuid=fbnode.plc_pcuid)

				sitehist.attemptReboot(host)
				print "send message for host %s try_reboot" % host
				if False and not fbpcu.test_is_ok() and \
					not found_within(recent_actions, 'pcuerror_notice', 3.0):

					args = {}
					if fbpcu:
						args['pcu_name'] = fbpcu.pcu_name()
						args['pcu_errors'] = fbpcu.pcu_errors()
						args['plc_pcuid'] = fbpcu.plc_pcuid
					else:
						args['pcu_name'] = "error looking up pcu name"
						args['pcu_errors'] = ""
						args['plc_pcuid'] = 0

					args['hostname'] = host
					sitehist.sendMessage('pcuerror_notice', **args)
					print "send message for host %s PCU Failure" % host
					

		# NOTE: non-intuitive is that found_between(try_reboot, 3.5, 1)
		# 		will be false for a day after the above condition is satisfied
		if False and nodehist.haspcu and nodehist.status in ['offline', 'down'] and \
			changed_greaterthan(nodehist.last_changed,1.5) and \
			not nodehist.firewall and \
			found_between(recent_actions, 'try_reboot', 3.5, 1) and \
			not found_within(recent_actions, 'pcufailed_notice', 3.5):
				
				# TODO: there MUST be a better way to do this... 
				# get fb node record for pcuid
				fbpcu = None
				fbnode = FindbadNodeRecord.get_latest_by(hostname=host)
				if fbnode:
					fbpcu = FindbadPCURecord.get_latest_by(plc_pcuid=fbnode.plc_pcuid)
				if fbpcu:
					pcu_name = fbpcu.pcu_name()
				else:
					pcu_name = "error looking up pcu name"

				# get fb pcu record for pcuid
				# send pcu failure message
				sitehist.sendMessage('pcufailed_notice', hostname=host, pcu_name=pcu_name)
				print "send message for host %s PCU Failure" % host

		if nodehist.status == 'failboot' and \
			changed_greaterthan(nodehist.last_changed, 0.25) and \
			not found_between(recent_actions, 'bootmanager_restore', 0.5, 0):
				# send down node notice
				# delay 0.5 days before retrying...

				print "send message for host %s bootmanager_restore" % host
				sitehist.runBootManager(host)
			#	sitehist.sendMessage('retry_bootman', hostname=host)

		if nodehist.status == 'down' and \
			changed_greaterthan(nodehist.last_changed, 2):
				if not nodehist.firewall and not found_within(recent_actions, 'down_notice', 3.5):
					# send down node notice
					sitehist.sendMessage('down_notice', hostname=host)
					print "send message for host %s down" % host

				#if nodehist.firewall and not found_within(recent_actions, 'firewall_notice', 3.5):
					# send down node notice
					#email_exception(host, "firewall_notice")
				#	sitehist.sendMessage('firewall_notice', hostname=host)
				#	print "send message for host %s down" % host

		node_count = node_count + 1
		print "time: ", time.strftime('%Y-%m-%d %H:%M:%S')
		sys.stdout.flush()
		session.flush()

	for i,site in enumerate(sitenames):
		sitehist = SiteInterface.get_or_make(loginbase=site)
		siteblack = BlacklistRecord.get_by(loginbase=site)
		skip_due_to_blacklist=False

		if siteblack and not siteblack.expired():
			print "skipping %s due to blacklist.  will expire %s" % (site, siteblack.willExpire() )
			skip_due_to_blacklist=True
			sitehist.clearPenalty()
			sitehist.applyPenalty()
			continue

		# TODO: make query only return records within a certin time range,
		# 		i.e. greater than 0.5 days ago. or 5 days, etc.
		recent_actions = sitehist.getRecentActions(loginbase=site)

		print "%s %s %s" % (i, sitehist.db.loginbase, sitehist.db.status)

		if sitehist.db.status == 'down':
			if sitehist.db.penalty_pause and \
				changed_greaterthan(sitehist.db.penalty_pause_time, 30):

				email_exception("", "clear pause penalty for site: %s" % sitehist.db.loginbase)
				sitehist.closeTicket()
				# NOTE: but preserve the penalty status.
				sitehist.clearPenaltyPause()

			if sitehist.db.message_id != 0 and \
				sitehist.db.message_status == 'open' and \
				not sitehist.db.penalty_pause:

				email_exception("", "pause penalty for site: %s" % sitehist.db.loginbase)
				sitehist.setPenaltyPause()

			if  not sitehist.db.penalty_pause and \
				not found_within(recent_actions, 'increase_penalty', 7) and \
				changed_greaterthan(sitehist.db.last_changed, 7):

				# TODO: catch errors
				sitehist.increasePenalty()
				sitehist.applyPenalty()
				sitehist.sendMessage('increase_penalty')

				print "send message for site %s penalty increase" % site

		if sitehist.db.status == 'good':
			# clear penalty
			# NOTE: because 'all clear' should have an indefinite status, we
			# 		have a boolean value rather than a 'recent action'
			if sitehist.db.penalty_applied or sitehist.db.penalty_pause:
				# send message that penalties are cleared.

				sitehist.clearPenalty()
				sitehist.applyPenalty()
				sitehist.sendMessage('clear_penalty')
				sitehist.closeTicket()

				print "send message for site %s penalty cleared" % site
				
			# check all nodes and pcus for this site; if they're all ok,
			# 		close the ticket, else leave it open.
			# NOTE: in the case where a PCU reboots and fails, a message is
			# 		sent, but the PCU may appear to be ok according to tests.
			# NOTE: Also, bootmanager sends messages regarding disks,
			# 		configuration, etc.  So, the conditions here are 'good'
			# 		rather than 'not down' as it is in sitebad.
			close_ticket = check_node_and_pcu_status_for(site)
			if close_ticket:
				sitehist.closeTicket()

		site_count = site_count + 1

		print "time: ", time.strftime('%Y-%m-%d %H:%M:%S')
		sys.stdout.flush()
		session.flush()

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
						quiet=False,)

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

	fbquery = HistoryNodeRecord.query.all()
	hostnames = [ n.hostname for n in fbquery ]
	
	fbquery = HistorySiteRecord.query.all()
	sitenames = [ s.loginbase for s in fbquery ]

	if config.site:
		# TODO: replace with calls to local db.  the api fails so often that
		# 		these calls should be regarded as unreliable.
		l_nodes = plccache.GetNodesBySite(config.site)
		filter_hostnames = [ n['hostname'] for n in l_nodes ]

		hostnames = filter(lambda x: x in filter_hostnames, hostnames)
		sitenames = [config.site]

	if config.node:
		hostnames = [ config.node ] 
		sitenames = [ plccache.plcdb_hn2lb[config.node] ]

	try:
		main(hostnames, sitenames)
		session.flush()
	except KeyboardInterrupt:
		print "Killed by interrupt"
		session.flush()
		sys.exit(0)
	except:
		email_exception()
		print traceback.print_exc();
		print "fail all..."
