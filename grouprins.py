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

from monitor import config
from monitor import util
from monitor import const
from monitor import database
from monitor import parser as parsermodule
from monitor.pcu import reboot
from monitor.wrapper import plc
api = plc.getAuthAPI()

import traceback
from optparse import OptionParser

from nodecommon import *
from nodequery import verify,query_to_dict,node_select
from monitor.model import *
import os

import time

import bootman 		# debug nodes
import mailmonitor 	# down nodes without pcu
from emailTxt import mailtxt
import sys

class Reboot(object):
	def __init__(self, fbnode):
		self.fbnode = fbnode

	def _send_pcunotice(self, host):
		args = {}
		args['hostname'] = host
		try:
			args['pcu_id'] = plc.getpcu(host)['pcu_id']
		except:
			args['pcu_id'] = host
			
		m = PersistMessage(host, mailtxt.pcudown_one[0] % args,
								 mailtxt.pcudown_one[1] % args, True, db='pcu_persistmessages')

		loginbase = plc.siteId(host)
		m.send([const.TECHEMAIL % loginbase])

	def pcu(self, host):
		# TODO: It should be possible to diagnose the various conditions of
		# 		the PCU here, and send different messages as appropriate.
		print "'%s'" % self.fbnode['pcu']
		if self.fbnode['pcu'] == "PCU" or "PCUOK" in self.fbnode['pcu']:
			self.action = "reboot.reboot('%s')" % host

			pflags = PersistFlags(host, 2*60*60*24, db='pcu_persistflags')
			#pflags.resetRecentFlag('pcutried')
			if not pflags.getRecentFlag('pcutried'):
				try:
					print "CALLING REBOOT!!!"
					ret = reboot.reboot(host)

					pflags.setRecentFlag('pcutried')
					pflags.save()
					return ret

				except Exception,e:
					print traceback.print_exc(); print e

					# NOTE: this failure could be an implementation issue on
					# 		our end.  So, extra notices are confusing...
					# self._send_pcunotice(host) 

					pflags.setRecentFlag('pcufailed')
					pflags.save()
					return False

			elif not pflags.getRecentFlag('pcu_rins_tried'):
				try:
					# set node to 'rins' boot state.
					print "CALLING REBOOT +++ RINS"
					plc.nodeBootState(host, 'rins')
					ret = reboot.reboot(host)

					pflags.setRecentFlag('pcu_rins_tried')
					pflags.save()
					return ret

				except Exception,e:
					print traceback.print_exc(); print e

					# NOTE: this failure could be an implementation issue on
					# 		our end.  So, extra notices are confusing...
					# self._send_pcunotice(host) 

					pflags.setRecentFlag('pcufailed')
					pflags.save()
					return False
			else:
				# we've tried the pcu recently, but it didn't work,
				# so did we send a message about it recently?
				if not pflags.getRecentFlag('pcumessagesent'): 

					self._send_pcunotice(host)

					pflags.setRecentFlag('pcumessagesent')
					pflags.save()

				# This will result in mail() being called next, to try to
				# engage the technical contact to take care of it also.
				print "RETURNING FALSE"
				return False

		else:
			print "NO PCUOK"
			self.action = "None"
			return False

	def mail(self, host):

		# Reset every 4 weeks or so
		pflags = PersistFlags(host, 27*60*60*24, db='mail_persistflags')
		if not pflags.getRecentFlag('endrecord'):
			node_end_record(host)
			pflags.setRecentFlag('endrecord')
			pflags.save()

		# Then in either case, run mailmonitor.reboot()
		self.action = "mailmonitor.reboot('%s')" % host
		try:
			return mailmonitor.reboot(host)
		except Exception, e:
			print traceback.print_exc(); print e
			return False

class RebootDebug(Reboot):

	def direct(self, host):
		self.action = "bootman.reboot('%s', config, None)" % host
		return bootman.reboot(host, config, None)
	
class RebootBoot(Reboot):

	def direct(self, host):
		self.action = "bootman.reboot('%s', config, 'reboot')" % host
		return bootman.reboot(host, config, 'reboot')

class RebootDown(Reboot):

	def direct(self, host):
		self.action = "None"
		return False    # this always fails, since the node will be down.

def set_node_to_rins(host, fb):

	node = api.GetNodes(host, ['boot_state', 'last_contact', 'last_updated', 'date_created'])
	record = {'observation' : node[0], 
			  'model' : 'USER_REQUEST', 
			  'action' : 'api.UpdateNode(%s, {"boot_state" : "rins"})' % host, 
			  'time' : time.time()}
	l = Log(host, record)

	ret = api.UpdateNode(host, {'boot_state' : 'rins'})
	if ret:
		# it's nice to see the current status rather than the previous status on the console
		node = api.GetNodes(host)[0]
		print l
		print "%-2d" % (i-1), nodegroup_display(node, fb)
		return l
	else:
		print "FAILED TO UPDATE NODE BOOT STATE : %s" % host
		return None


try:
	rebootlog = database.dbLoad("rebootlog")
except:
	rebootlog = LogRoll()

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

# COLLECT nodegroups, nodes and node lists
if config.nodegroup:
	ng = api.GetNodeGroups({'name' : config.nodegroup})
	nodelist = api.GetNodes(ng[0]['node_ids'])
	hostnames = [ n['hostname'] for n in nodelist ]

if config.site:
	site = api.GetSites(config.site)
	l_nodes = api.GetNodes(site[0]['node_ids'], ['hostname'])
	hostnames = [ n['hostname'] for n in l_nodes ]

if config.node or config.nodelist:
	if config.node: hostnames = [ config.node ] 
	else: hostnames = util.file.getListFromFile(config.nodelist)

fbquery = FindbadNodeRecord.get_all_latest()
fb_nodelist = [ n.hostname for n in fbquery ]

if config.nodeselect:
	hostnames = node_select(config.nodeselect, fb_nodelist)

if config.findbad:
	# rerun findbad with the nodes in the given nodes.
	file = "findbad.txt"
	util.file.setFileFromList(file, hostnames)
	os.system("./findbad.py --cachenodes --increment --nodelist %s" % file)
	# TODO: shouldn't we reload the node list now?

l_blacklist = database.if_cached_else(1, "l_blacklist", lambda : [])
# commands:
i = 1
count = 1
#print "hosts: %s" % hostnames
for host in hostnames:

	#if 'echo' in host or 'hptest-1' in host: continue

	try:
		try:
			node = api.GetNodes(host)[0]
		except:
			print traceback.print_exc(); 
			print "FAILED GETNODES for host: %s" % host
			continue
			
		print "%-2d" % i, nodegroup_display(node, fb)
		i += 1
		if i-1 <= int(config.skip): continue
		if host in l_blacklist:
			print "%s is blacklisted.  Skipping." % host
			continue

		if config.stopselect:
			dict_query = query_to_dict(config.stopselect)
			fbnode = fb['nodes'][host]['values']
			observed_state = get_current_state(fbnode)

			if verify(dict_query, fbnode) and observed_state != "dbg ":
				# evaluates to true, therefore skip.
				print "%s evaluates true for %s ; skipping..." % ( config.stopselect, host )
				try:
					# todo: clean up act_all record here.
					# todo: send thank you, etc.
					mailmonitor.reboot(host)
				except Exception, e:
					print traceback.print_exc(); print e

				continue
			#else:
				#print "%s failed to match %s: -%s-" % ( host, dict_query, observed_state )
				#sys.exit(1)

		if not config.force and rebootlog.find(host, {'action' : ".*reboot"}, 60*60*2):
			print "recently rebooted %s.  skipping... " % host
			continue

		if config.reboot:

			fbnode = fb['nodes'][host]['values']
			observed_state = get_current_state(fbnode)

			if	 observed_state == "dbg ":
				o = RebootDebug(fbnode)

			elif observed_state == "boot" :
				if config.rins:
					l = set_node_to_rins(host, fb)
					if l: rebootlog.add(l)

				o = RebootBoot(fbnode)

			elif observed_state == "down":
				if config.rins:
					l = set_node_to_rins(host, fb)
					if l: rebootlog.add(l)

				o = RebootDown(fbnode)


			if o.direct(host):
				record = {'observation' : "DIRECT_SUCCESS: %s" % observed_state, 
						  'action' : o.action,
						  'model' : "none",
						  'time' : time.time()}
			elif o.pcu(host):
				record = {'observation' : "PCU_SUCCESS: %s" % observed_state, 
						  'action' : o.action,
						  'model' : "none",
						  'time' : time.time()}
			elif o.mail(host):
				record = {'observation' : "MAIL_SUCCESS: %s" % observed_state, 
						  'action' : o.action,
						  'model' : "none",
						  'time' : time.time()}
			else:
				record = {'observation' : "REBOOT_FAILED: %s" %  observed_state,
						  'action' : "log failure",
						  'model' : "none",
						  'time' : time.time()}

				print "ALL METHODS OF RESTARTING %s FAILED" % host
				args = {}
				args['hostname'] = host
				#m = PersistMessage(host, "ALL METHODS FAILED for %(hostname)s" % args,
				#							 "CANNOT CONTACT", False, db='suspect_persistmessages')
				#m.reset()
				#m.send(['monitor-list@lists.planet-lab.org'])

			l = Log(host, record)
			print l
			rebootlog.add(l)
	except KeyboardInterrupt:
		print "Killed by interrupt"
		sys.exit(0)
	except:
		print traceback.print_exc();
		print "Continuing..."

	time.sleep(1)
	if count % 10 == 0:
		print "Saving rebootlog"
		database.dbDump("rebootlog", rebootlog)
		wait_time = int(config.timewait)
		print "Sleeping %d minutes" % wait_time
		ti = 0
		print "Minutes slept: ",
		sys.stdout.flush()
		while ti < wait_time:
			print "%s" % ti,
			sys.stdout.flush()
			time.sleep(60)
			ti = ti+1

	count = count + 1

print "Saving rebootlog"
database.dbDump("rebootlog", rebootlog)
