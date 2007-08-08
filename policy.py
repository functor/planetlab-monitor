#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: policy.py,v 1.15 2007/07/03 19:58:34 soltesz Exp $
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
import sys
import reboot
import soltesz
import string
from printbadbysite import cmpCategoryVal
from config import config
print "policy"
config = config()

DAT="./monitor.dat"

logger = logging.getLogger("monitor")

# Time to enforce policy
POLSLEEP = 7200

# Where to email the summary
SUMTO = "soltesz@cs.princeton.edu"
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

TECH=1
PI=2
USER=4
ADMIN=8

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
def array_to_priority_map(array):
	""" Create a mapping where each entry of array is given a priority equal
	to its position in the array.  This is useful for subsequent use in the
	cmpMap() function."""
	map = {}
	count = 0
	for i in array:
		map[i] = count
		count += 1
	return map

def getdebug():
	return config.debug

class Merge(Thread):
	def __init__(self, l_merge, toRT):
		self.toRT = toRT
		self.merge_list = l_merge
		# the hostname to loginbase mapping
		self.plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")

		# Previous actions taken on nodes.
		self.act_all = soltesz.if_cached_else(1, "act_all", lambda : {})
		self.findbad = soltesz.if_cached_else(1, "findbad", lambda : {})

		self.cache_all = soltesz.if_cached_else(1, "act_all", lambda : {})
		self.sickdb = {}
		self.mergedb = {}
		Thread.__init__(self)

	def run(self):
		# populate sickdb
		self.accumSickSites()
		# read data from findbad and act_all
		self.mergeActionsAndBadDB()
		# pass node_records to RT
		self.sendToRT()

	def accumSickSites(self):
		"""
		Take all nodes, from l_diagnose, look them up in the act_all database, 
		and insert them into sickdb[] as:

			sickdb[loginbase][nodename] = fb_record
		"""
		# look at all problems reported by findbad
		l_nodes = self.findbad['nodes'].keys()
		count = 0
		for nodename in l_nodes:
			if nodename not in self.merge_list:
				continue		# skip this node, since it's not wanted

			count += 1
			loginbase = self.plcdb_hn2lb[nodename]
			values = self.findbad['nodes'][nodename]['values']

			fb_record = {}
			fb_record['nodename'] = nodename
			fb_record['category'] = values['category']
			fb_record['state'] = values['state']
			fb_record['comonstats'] = values['comonstats']
			fb_record['kernel'] = self.getKernel(values['kernel'])
			fb_record['stage'] = "findbad"
			fb_record['message'] = None
			fb_record['bootcd'] = values['bootcd']
			fb_record['args'] = None
			fb_record['info'] = None
			fb_record['time'] = time.time()
			fb_record['date_created'] = time.time()

			if loginbase not in self.sickdb:
				self.sickdb[loginbase] = {}

			self.sickdb[loginbase][nodename] = fb_record

		print "Found %d nodes" % count

	def getKernel(self, unamestr):
		s = unamestr.split()
		if len(s) > 2:
			return s[2]
		else:
			return ""

	def mergeActionsAndBadDB(self):	
		"""
		- Look at the sick node_records as reported in findbad, 
		- Then look at the node_records in act_all.  

		There are four cases:
		1) Problem in findbad, no problem in act_all
			this ok, b/c it just means it's a new problem
		2) Problem in findbad, problem in act_all
			-Did the problem get better or worse?  
				-If Same, or Worse, then continue looking for open tickets.
				-If Better, or No problem, then "back-off" penalties.
					This judgement may need to wait until 'Diagnose()'

		3) No problem in findbad, problem in act_all
			The the node is operational again according to Findbad()

		4) No problem in findbad, no problem in act_all
			There won't be a record in either db, so there's no code.
		"""

		sorted_sites = self.sickdb.keys()
		sorted_sites.sort()
		# look at all problems reported by findbad
		for loginbase in sorted_sites:
			d_fb_nodes = self.sickdb[loginbase]
			sorted_nodes = d_fb_nodes.keys()
			sorted_nodes.sort()
			for nodename in sorted_nodes:
				fb_record = self.sickdb[loginbase][nodename]
				x = fb_record
				if loginbase not in self.mergedb:
					self.mergedb[loginbase] = {}

				# We must compare findbad state with act_all state
				if nodename not in self.act_all:
					# 1) ok, b/c it's a new problem. set ticket_id to null
					self.mergedb[loginbase][nodename] = {} 
					self.mergedb[loginbase][nodename].update(x)
					self.mergedb[loginbase][nodename]['ticket_id'] = ""
					self.mergedb[loginbase][nodename]['prev_category'] = None
				else: 
					y = self.act_all[nodename][0]

					# skip if end-stage
					if 'stage' in y and "monitor-end-record" in y['stage']:
						continue

					# for legacy actions
					if 'bucket' in y and y['bucket'][0] == 'dbg':
						# Only bootcd debugs made it to the act_all db.
						y['prev_category'] = "OLDBOOTCD"
					elif 'bucket' in y and y['bucket'][0] == 'down':
						y['prev_category'] = "ERROR"
					elif 'bucket' not in y:
						# for all other actions, just carry over the
						# previous category
						y['prev_category'] = y['category']
					else:
						print "UNKNOWN state for record: %s" % y
						sys.exit(1)
					# determine through translation, if the buckets match
					#if 'category' in y and x['category'] == y['category']:
					#	b_match = True
					#elif x['category'] == "OLDBOOTCD" and y['bucket'][0] == 'dbg':
					#	b_match = True
					#elif x['category'] == "ERROR" and y['bucket'][0] == 'down':
					#	b_match = True
					#else:
					#	b_match = False

					#if b_match: 
					#	# 2b) ok, b/c they agree that there's still a problem..
					#	# 2b) Comon & Monitor still agree; RT ticket?
					#	y['prev_category'] = y['category']
					#else:
					#	# 2a) mismatch, need a policy for how to resolve
					#	#     resolution will be handled in __diagnoseNode()
					#	#	  for now just record the two categories.
					#	#if x['category'] == "PROD" and x['state'] == "BOOT" and \
					#	# ( y['bucket'][0] == 'down' or  y['bucket'][0] == 'dbg'):
					#	print "FINDBAD and MONITOR have a mismatch: %s vs %s" % \
					#				(x['category'], y['bucket'])


					self.mergedb[loginbase][nodename] = {}
					self.mergedb[loginbase][nodename].update(y)
					self.mergedb[loginbase][nodename]['comonstats'] = x['comonstats']
					self.mergedb[loginbase][nodename]['category']   = x['category']
					self.mergedb[loginbase][nodename]['state'] = x['state']
					self.mergedb[loginbase][nodename]['kernel']=x['kernel']
					self.mergedb[loginbase][nodename]['bootcd']=x['bootcd']
					# delete the entry from cache_all to keep it out of case 3)
					del self.cache_all[nodename]

		# 3) nodes that remin in cache_all were not identified by findbad.
		# 	 Do we keep them or not?
		#   NOTE: i think that since the categories are performed before this
		#   		step now, and by a monitor-controlled agent.

		# TODO: This does not work correctly.  Do we need this? 
		#for hn in self.cache_all.keys():
		#	y = self.act_all[hn][0]
		#	if 'monitor' in y['bucket']:
		#		loginbase = self.plcdb_hn2lb[hn] 
		#		if loginbase not in self.sickdb:
		#			self.sickdb[loginbase] = {}
		#		self.sickdb[loginbase][hn] = y
		#	else:
		#		del self.cache_all[hn]

		print "len of cache_all: %d" % len(self.cache_all.keys())
		return

	def sendToRT(self):
		sorted_sites = self.mergedb.keys()
		sorted_sites.sort()
		# look at all problems reported by merge
		for loginbase in sorted_sites:
			d_merge_nodes = self.mergedb[loginbase]
			for nodename in d_merge_nodes.keys():
				record = self.mergedb[loginbase][nodename]
				self.toRT.put(record)

		# send signal to stop reading
		self.toRT.put(None)
		return

class Diagnose(Thread):
	def __init__(self, fromRT):
		self.fromRT = fromRT
		self.plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")

		self.diagnose_in = {}
		self.diagnose_out = {}
		Thread.__init__(self)

	def print_stats(self, key, stats):
		print "%20s : %d" % (key, stats[key])

	def run(self):
		self.accumSickSites()

		print "Accumulated %d sick sites" % len(self.diagnose_in.keys())
		logger.debug("Accumulated %d sick sites" % len(self.diagnose_in.keys()))

		try:
			stats = self.diagnoseAll()
		except Exception, err:
			print "----------------"
			import traceback
			print traceback.print_exc()
			print err
			#if config.policysavedb:
			sys.exit(1)

		self.print_stats("sites", stats)
		self.print_stats("sites_diagnosed", stats)
		self.print_stats("nodes_diagnosed", stats)

		if config.policysavedb:
			print "Saving Databases... diagnose_out"
			soltesz.dbDump("diagnose_out", self.diagnose_out)

	def accumSickSites(self):
		"""
		Take all nodes, from l_diagnose, look them up in the diagnose_out database, 
		and insert them into diagnose_in[] as:

			diagnose_in[loginbase] = [diag_node1, diag_node2, ...]
		"""
		while 1:
			node_record = self.fromRT.get(block = True)
			if node_record == None:
				break;

			nodename = node_record['nodename']
			loginbase = self.plcdb_hn2lb[nodename]

			if loginbase not in self.diagnose_in:
				self.diagnose_in[loginbase] = {}

			self.diagnose_in[loginbase][nodename] = node_record

		return

	def diagnoseAll(self):
		i_sites = 0
		i_sites_diagnosed = 0
		i_nodes_diagnosed = 0
		i_nodes_actedon = 0
		i_sites_emailed = 0
		l_allsites = []

		sorted_sites = self.diagnose_in.keys()
		sorted_sites.sort()
		l_diagnosed_all = []
		for loginbase in sorted_sites:
			l_allsites += [loginbase]

			d_diag_nodes = self.diagnose_in[loginbase]
			l_diag_records = self.__diagnoseSite(loginbase, d_diag_nodes)
			l_diagnosed_all += l_diag_records
			
			if len(l_diag_records) > 0:
				i_nodes_diagnosed += len(l_diag_records)
				i_sites_diagnosed += 1
			i_sites += 1

		self.diagnose_out= {}
		for diag_record in l_diagnosed_all:
			nodename = diag_record['nodename']
			loginbase = self.plcdb_hn2lb[nodename]

			if loginbase not in self.diagnose_out:
				self.diagnose_out[loginbase] = {}

			self.diagnose_out[loginbase][nodename] = diag_record

		return {'sites': i_sites, 
				'sites_diagnosed': i_sites_diagnosed, 
				'nodes_diagnosed': i_nodes_diagnosed, 
				'allsites':l_allsites}

		pass
		
	def __getDaysDown(self, diag_record, nodename):
		daysdown = -1
		if diag_record['comonstats']['sshstatus'] != "null":
			daysdown = int(diag_record['comonstats']['sshstatus']) // (60*60*24)
		elif diag_record['comonstats']['lastcotop'] != "null":
			daysdown = int(diag_record['comonstats']['lastcotop']) // (60*60*24)
		else:
			daysdown = -1
		return daysdown

	def __getStrDaysDown(self, diag_record, nodename):
		daysdown = self.__getDaysDown(diag_record, nodename)
		if daysdown > 0:
			return "(%d days down)"%daysdown
		else:
			return "Unknown number of days"

	def __getCDVersion(self, diag_record, nodename):
		cdversion = ""
		#print "Getting kernel for: %s" % diag_record['nodename']
		cdversion = diag_record['kernel']
		return cdversion

	def __diagnoseSite(self, loginbase, d_diag_nodes):
		"""
		rec_sitelist is a diagnose_in entry: 
		"""
		diag_list = []
		sorted_nodes = d_diag_nodes.keys()
		sorted_nodes.sort()
		for nodename in sorted_nodes:
			node_record = d_diag_nodes[nodename]
			diag_record = self.__diagnoseNode(loginbase, node_record)

			if diag_record != None:
				diag_list += [ diag_record ]

		return diag_list

	def diagRecordByCategory(self, node_record):
		nodename = node_record['nodename']
		category = node_record['category']
		state    = node_record['state']
		loginbase = self.plcdb_hn2lb[nodename]
		diag_record = None

		if  "ERROR" in category:	# i.e. "DOWN"
			diag_record = {}
			diag_record.update(node_record)
			daysdown = self.__getDaysDown(diag_record, nodename) 
			if daysdown >= 0 and daysdown < 7:
				format = "DIAG: %20s : %-40s Down only %s days  NOTHING DONE"
				print format % (loginbase, nodename, daysdown)
				return None

			s_daysdown = self.__getStrDaysDown(diag_record, nodename)
			diag_record['message'] = emailTxt.mailtxt.newdown
			diag_record['args'] = {'nodename': nodename}
			diag_record['info'] = (nodename, s_daysdown, "")
			diag_record['log'] = "DOWN: %20s : %-40s == %20s %s" % \
					(loginbase, nodename, diag_record['info'], diag_record['ticket_id']),

		elif "OLDBOOTCD" in category:
			# V2 boot cds as determined by findbad
			s_daysdown = self.__getStrDaysDown(node_record, nodename)
			s_cdversion = self.__getCDVersion(node_record, nodename)
			diag_record = {}
			diag_record.update(node_record)
			#if "2.4" in diag_record['kernel'] or "v2" in diag_record['bootcd']:
			diag_record['message'] = emailTxt.mailtxt.newbootcd
			diag_record['args'] = {'nodename': nodename}
			diag_record['info'] = (nodename, s_daysdown, s_cdversion)
			diag_record['log'] = "BTCD: %20s : %-40s == %20s %20s %s" % \
									(loginbase, nodename, diag_record['kernel'], 
									 diag_record['bootcd'], diag_record['ticket_id']),

		elif "PROD" in category:
			if "DEBUG" in state:
				# Not sure what to do with these yet.  Probably need to
				# reboot, and email.
				print "DEBG: %20s : %-40s  NOTHING DONE" % (loginbase, nodename)
				return None
			elif "BOOT" in state:
				# no action needed.
				# TODO: remove penalties, if any are applied.
				if 'improvement' in node_record['stage']:
					# then we need to pass this on to 'action'
					diag_record = {}
					diag_record.update(node_record)
					diag_record['message'] = emailTxt.mailtxt.newthankyou
					diag_record['args'] = {'nodename': nodename}
					diag_record['info'] = (nodename, node_record['prev_category'], 
													 node_record['category'])
					diag_record['log'] = "IMPR: %20s : %-40s == %20s %20s %s" % \
									(loginbase, nodename, diag_record['stage'], 
									 state, category),
					return diag_record
				else:
					return None
			else:
				# unknown
				pass
		elif "ALPHA"    in category:
			pass
		elif "clock_drift" in category:
			pass
		elif "dns"    in category:
			pass
		elif "filerw"    in category:
			pass
		else:
			print "Unknown category!!!! %s" % category
			sys.exit(1)

		return diag_record

	def __diagnoseNode(self, loginbase, node_record):
		# TODO: change the format of the hostname in this 
		#		record to something more natural.
		nodename 	  = node_record['nodename']
		category 	  = node_record['category']
		prev_category = node_record['prev_category']
		state    	  = node_record['state']

		val = cmpCategoryVal(category, prev_category)
		if val == -1:
			# current category is worse than previous, carry on
			pass
		elif val == 1:
			# current category is better than previous
			# TODO: too generous for now, but will be handled correctly
			node_record['stage'] = 'improvement'
		else:
			#values are equal, carry on.
			pass
			
		#### COMPARE category and prev_category
		# if not_equal
		#	then assign a stage based on relative priorities
		# else equal
		#	then check category for stats.
		diag_record = self.diagRecordByCategory(node_record)
		if diag_record == None:
			return None

		#### found_RT_ticket
		# TODO: need to record time found, and maybe add a stage for acting on it...
		if 'found_rt_ticket' in diag_record and \
			diag_record['found_rt_ticket'] is not None:
			if diag_record['stage'] is not 'improvement':
				diag_record['stage'] = 'ticket_waitforever'
				
		current_time = time.time()
		delta = current_time - diag_record['time']

		message = diag_record['message']
		act_record = {}
		act_record.update(diag_record)

		#### DIAGNOSE STAGES 
		#print "%s has stage %s" % (nodename, diag_record['stage'])
		if   'findbad' in diag_record['stage']:
			# The node is bad, and there's no previous record of it.
			act_record['email'] = TECH		# addative emails
			act_record['action'] = 'noop'
			act_record['message'] = message[0]
			act_record['stage'] = 'stage_actinoneweek'

		elif 'improvement' in diag_record['stage']:
			# - backoff previous squeeze actions (slice suspend, nocreate)
			# TODO: add a backoff_squeeze section... Needs to runthrough
			act_record['action'] = 'close_rt'
			act_record['message'] = message[0]
			act_record['stage'] = 'monitor-end-record'

		elif 'actinoneweek' in diag_record['stage']:
			act_record['email'] = TECH | PI		# addative emails
			if delta >= 7 * SPERDAY: 
				act_record['stage'] = 'stage_actintwoweeks'
				act_record['message'] = message[1]
				act_record['action'] = 'nocreate' 
			elif delta >= 3* SPERDAY and not 'second-mail-at-oneweek' in act_record:
				act_record['message'] = message[1]
				act_record['action'] = 'sendmailagain-waitforoneweekaction' 
				act_record['second-mail-at-oneweek'] = True
			else:
				act_record['message'] = None
				act_record['action'] = 'waitforoneweekaction' 

		elif 'actintwoweeks' in diag_record['stage']:
			act_record['email'] = TECH | PI | USER		# addative emails
			if delta >= 14 * SPERDAY:
				act_record['stage'] = 'stage_waitforever'
				act_record['message'] = message[2]
				act_record['action'] = 'suspendslices'
				act_record['time'] = current_time		# reset clock for waitforever
			elif delta >= 10* SPERDAY and not 'second-mail-at-twoweeks' in act_record:
				act_record['message'] = message[2]
				act_record['action'] = 'sendmailagain-waitfortwoweeksaction' 
				act_record['second-mail-at-twoweeks'] = True
			else:
				act_record['message'] = None
				act_record['action'] = 'waitfortwoweeksaction'

		elif 'ticket_waitforever' in diag_record['stage']:
			act_record['email'] = TECH
			if 'first-found' not in act_record:
				act_record['first-found'] = True
				act_record['action'] = 'ticket_waitforever'
				act_record['message'] = None
				act_record['time'] = current_time
			else:
				if delta >= 7*SPERDAY:
					act_record['action'] = 'email-againticket_waitforever'
					act_record['message'] = message[0]
					act_record['time'] = current_time		# reset clock
				else:
					act_record['action'] = 'ticket_waitforever'
					act_record['message'] = None

		elif 'waitforever' in diag_record['stage']:
			# more than 3 days since last action
			# TODO: send only on weekdays.
			# NOTE: expects that 'time' has been reset before entering waitforever stage
			if delta >= 3*SPERDAY:
				act_record['action'] = 'email-againwaitforever'
				act_record['message'] = message[0]
				act_record['time'] = current_time		# reset clock
			else:
				act_record['action'] = 'waitforever'
				act_record['message'] = None

		else:
			# There is no action to be taken, possibly b/c the stage has
			# already been performed, but diagnose picked it up again.
			# two cases, 
			#	1. stage is unknown, or 
			#	2. delta is not big enough to bump it to the next stage.
			# TODO: figure out which. for now assume 2.
			print "UNKNOWN!!? %s" % nodename
			act_record['action'] = 'unknown'
			act_record['message'] = message[0]
			print "Exiting..."
			sys.exit(1)

		print "%s" % act_record['log'],
		print "%15s" % act_record['action']
		return act_record


class SiteAction:
	def __init__(self, parameter_names=['hostname', 'ticket_id']):
		self.parameter_names = parameter_names
	def checkParam(self, args):
		for param in self.parameter_names:
			if param not in args:
				raise Exception("Parameter %s not provided in args"%param)
	def run(self, args):
		self.checkParam(args)
		return self._run(args)
	def _run(self, args):
		pass

class SuspendAction(SiteAction):
	def _run(self, args):
		return plc.suspendSlices(args['hostname'])

class RemoveSliceCreation(SiteAction):
	def _run(self, args):
		return plc.removeSliceCreation(args['hostname'])

class BackoffActions(SiteAction):
	def _run(self, args):
		plc.enableSlices(args['hostname'])
		plc.enableSliceCreation(args['hostname'])
		return True

# TODO: create class for each action below, 
#		allow for lists of actions to be performed...

def close_rt_backoff(args):
	mailer.closeTicketViaRT(args['ticket_id'], "Ticket CLOSED automatically by SiteAssist.")
	plc.enableSlices(args['hostname'])
	plc.enableSliceCreation(args['hostname'])
	return

class Action(Thread):
	def __init__(self, l_action):
		self.l_action = l_action

		# the hostname to loginbase mapping
		self.plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")

		# Actions to take.
		self.diagnose_db = soltesz.if_cached_else(1, "diagnose_out", lambda : {})
		# Actions taken.
		self.act_all   = soltesz.if_cached_else(1, "act_all", lambda : {})

		# A dict of actions to specific functions. PICKLE doesnt' like lambdas.
		self.actions = {}
		self.actions['suspendslices'] = lambda args: plc.suspendSlices(args['hostname'])
		self.actions['nocreate'] = lambda args: plc.removeSliceCreation(args['hostname'])
		self.actions['close_rt'] = lambda args: close_rt_backoff(args)
		self.actions['rins'] = lambda args: plc.nodeBootState(args['hostname'], "rins")	
		self.actions['noop'] = lambda args: args
		self.actions['ticket_waitforever'] = lambda args: args
		self.actions['waitforever'] = lambda args: args
		self.actions['unknown'] = lambda args: args
		self.actions['waitforoneweekaction'] = lambda args: args
		self.actions['waitfortwoweeksaction'] = lambda args: args
		self.actions['sendmailagain-waitforoneweekaction'] = lambda args: args
		self.actions['sendmailagain-waitfortwoweeksaction'] = lambda args: args
		self.actions['email-againwaitforever'] = lambda args: args
		self.actions['email-againticket_waitforever'] = lambda args: args
				

		self.sickdb = {}
		Thread.__init__(self)

	def run(self):
		self.accumSites()
		print "Accumulated %d sick sites" % len(self.sickdb.keys())
		logger.debug("Accumulated %d sick sites" % len(self.sickdb.keys()))

		try:
			stats = self.analyseSites()
		except Exception, err:
			print "----------------"
			import traceback
			print traceback.print_exc()
			print err
			if config.policysavedb:
				print "Saving Databases... act_all"
				soltesz.dbDump("act_all", self.act_all)
			sys.exit(1)

		self.print_stats("sites", stats)
		self.print_stats("sites_diagnosed", stats)
		self.print_stats("nodes_diagnosed", stats)
		self.print_stats("sites_emailed", stats)
		self.print_stats("nodes_actedon", stats)
		print string.join(stats['allsites'], ",")

		if config.policysavedb:
			print "Saving Databases... act_all"
			#soltesz.dbDump("policy.eventlog", self.eventlog)
			# TODO: remove 'diagnose_out', 
			#	or at least the entries that were acted on.
			soltesz.dbDump("act_all", self.act_all)

	def accumSites(self):
		"""
		Take all nodes, from l_action, look them up in the diagnose_db database, 
		and insert them into sickdb[] as:

		This way only the given l_action nodes will be acted on regardless
		of how many from diagnose_db are available.

			sickdb[loginbase][nodename] = diag_record
		"""
		# TODO: what if l_action == None ?
		for nodename in self.l_action:

			loginbase = self.plcdb_hn2lb[nodename]

			if loginbase in self.diagnose_db and \
				nodename in self.diagnose_db[loginbase]:

				diag_record = self.diagnose_db[loginbase][nodename]

				if loginbase not in self.sickdb:
					self.sickdb[loginbase] = {}

				self.sickdb[loginbase][nodename] = diag_record
		return

	def __emailSite(self, loginbase, roles, message, args):
		"""
		loginbase is the unique site abbreviation, prepended to slice names.
		roles contains TECH, PI, USER roles, and derive email aliases.
		record contains {'message': [<subj>,<body>], 'args': {...}} 
		"""
		ticket_id = 0
		args.update({'loginbase':loginbase})

		if not config.mail and not config.debug and config.bcc:
			roles = ADMIN
		if config.mail and config.debug:
			roles = ADMIN

		# build targets
		contacts = []
		if ADMIN & roles:
			contacts += [config.email]
		if TECH & roles:
			contacts += [TECHEMAIL % loginbase]
		if PI & roles:
			contacts += [PIEMAIL % loginbase]
		if USER & roles:
			slices = plc.slices(loginbase)
			if len(slices) >= 1:
				for slice in slices:
					contacts += [SLICEMAIL % slice]
				print "SLIC: %20s : %d slices" % (loginbase, len(slices))
			else:
				print "SLIC: %20s : 0 slices" % loginbase

		try:
			subject = message[0] % args
			body = message[1] % args
			if ADMIN & roles:
				# send only to admin
				if 'ticket_id' in args:
					subj = "Re: [PL #%s] %s" % (args['ticket_id'], subject)
				else:
					subj = "Re: [PL noticket] %s" % subject
				mailer.email(subj, body, contacts)
				ticket_id = args['ticket_id']
			else:
				#if 'ticket_id' in args and 'ticket_id' != "":
				#	# Reformat Subject to include Ticket_ID for RT
				#	subj = "Re: [PL #%s] %s" % (args['ticket_id'], subject)
				#	# RT remembers old contacts, so only add new users
				#	mailer.email(subj, body, ['monitor@planet-lab.org'] + contacts)
				#	ticket_id = args['ticket_id']
				#else:
				#	ticket_id = mailer.emailViaRT(subject, body, contacts)	
				ticket_id = mailer.emailViaRT(subject, body, contacts, args['ticket_id'])
		except Exception, err:
			print "exception on message:"
			import traceback
			print traceback.print_exc()
			print message

		return ticket_id


	def _format_diaginfo(self, diag_node):
		info = diag_node['info']
		if diag_node['stage'] == 'monitor-end-record':
			hlist = "    %s went from '%s' to '%s'\n" % (info[0], info[1], info[2]) 
		else:
			hlist = "    %s %s - %s\n" % (info[0], info[2], info[1]) #(node,ver,daysdn)
		return hlist

	def __actOnSite(self, loginbase, site_record):
		i_nodes_actedon = 0
		i_nodes_emailed = 0
		b_squeeze = config.squeeze

		act_recordlist = []

		for nodename in site_record.keys():
			diag_record = site_record[nodename]
			act_record  = self.__actOnNode(diag_record)
			act_recordlist += [act_record]

		count_up = self.currentUpAtSite(loginbase)
		if count_up < MINUP:
			print "SITE: %20s : %d nodes up" % (loginbase, count_up)
		else:
			print "SITE: %20s : %d nodes up" % (loginbase, count_up)
			# There may be a second penalty regardless of which stage it's in.
			# TODO: check how long this has occurred.

		email_args = {}
		email_args['hostname_list'] = ""
		for act_record in act_recordlist:
			email_args['hostname_list'] += act_record['msg_format']
			email_args['hostname'] = act_record['nodename']
			if 'ticket_id' in act_record:
				email_args['ticket_id'] = act_record['ticket_id']

		# Send email, perform node action
		# TODO: only send one email per site for a given problem...
		if len(act_recordlist) > 0:
			act_record = act_recordlist[0]

			# send message before squeezing, b/c 
			if act_record['message'] != None:
		 		ticket_id = self.__emailSite(loginbase, act_record['email'], 
							 act_record['message'], email_args)

				# Add ticket_id to ALL nodenames
				for act_record in act_recordlist:
					nodename = act_record['nodename']
					# update node record with RT ticket_id
					self.act_all[nodename][0]['ticket_id'] = "%s" % ticket_id
					if config.mail: i_nodes_emailed += 1

			# TODO: perform the most severe action?
			if b_squeeze:
				act_key = act_record['action']
				self.actions[act_key](email_args)
				i_nodes_actedon += 1
		
		if config.policysavedb:
			print "Saving Databases... act_all, diagnose_out"
			soltesz.dbDump("act_all", self.act_all)
			# remove site record from diagnose_out, it's in act_all as done.
			del self.diagnose_db[loginbase]
			soltesz.dbDump("diagnose_out", self.diagnose_db)

		print "Hit enter to continue..."
		sys.stdout.flush()
		line = sys.stdin.readline()

		return (i_nodes_actedon, i_nodes_emailed)

	def __actOnNode(self, diag_record):
		nodename = diag_record['nodename']
		message = diag_record['message']
		info	= diag_record['info']

		act_record = {}
		act_record.update(diag_record)
		act_record['nodename'] = nodename
		act_record['msg_format'] = self._format_diaginfo(diag_record)

		print "%s" % act_record['log'],
		print "%15s" % act_record['action']

		if act_record['stage'] is not 'monitor-end-record':
			if nodename not in self.act_all: 
				self.act_all[nodename] = []

			self.act_all[nodename].insert(0,act_record)
		else:
			print "Not recording %s in act_all" % nodename

		return act_record

	def analyseSites(self):
		i_sites = 0
		i_sites_diagnosed = 0
		i_nodes_diagnosed = 0
		i_nodes_actedon = 0
		i_sites_emailed = 0
		l_allsites = []

		sorted_sites = self.sickdb.keys()
		sorted_sites.sort()
		for loginbase in sorted_sites:
			site_record = self.sickdb[loginbase]
			
			i_nodes_diagnosed += len(site_record.keys())
			i_sites_diagnosed += 1

			(na,ne) = self.__actOnSite(loginbase, site_record)

			i_sites += 1
			i_nodes_actedon += na
			i_sites_emailed += ne

			l_allsites += [loginbase]

		return {'sites': i_sites, 
				'sites_diagnosed': i_sites_diagnosed, 
				'nodes_diagnosed': i_nodes_diagnosed, 
				'sites_emailed': i_sites_emailed, 
				'nodes_actedon': i_nodes_actedon, 
				'allsites':l_allsites}

	def print_stats(self, key, stats):
		print "%20s : %d" % (key, stats[key])



	#"""
	#Prints, logs, and emails status of up nodes, down nodes, and buckets.
	#"""
	#def status(self):
	#	sub = "Monitor Summary"
	#	msg = "\nThe following nodes were acted upon:  \n\n"
	#	for (node, (type, date)) in self.emailed.items():
	#		# Print only things acted on today.
	#		if (time.gmtime(time.time())[2] == time.gmtime(date)[2]):
	#			msg +="%s\t(%s)\t%s\n" %(node, type, time.ctime(date))
	#	msg +="\n\nThe following sites have been 'squeezed':\n\n"
	#	for (loginbase, (date, type)) in self.squeezed.items():
	#		# Print only things acted on today.
	#		if (time.gmtime(time.time())[2] == time.gmtime(date)[2]):
	#			msg +="%s\t(%s)\t%s\n" %(loginbase, type, time.ctime(date))
	#	mailer.email(sub, msg, [SUMTO])
	#	logger.info(msg)
	#	return 

	#"""
	#Store/Load state of emails.  When, where, what.
	#"""
	#def emailedStore(self, action):
	#	try:
	#		if action == "LOAD":
	#			f = open(DAT, "r+")
	#			logger.info("POLICY:  Found and reading " + DAT)
	#			self.emailed.update(pickle.load(f))
	#		if action == "WRITE":
	#			f = open(DAT, "w")
	#			#logger.debug("Writing " + DAT)
	#			pickle.dump(self.emailed, f)
	#		f.close()
	#	except Exception, err:
	#		logger.info("POLICY:  Problem with DAT, %s" %err)

	"""
	Returns number of up nodes as the total number *NOT* in act_all with a
	stage other than 'steady-state' .
	"""
	def currentUpAtSite(self, loginbase):
		allsitenodes = plc.getSiteNodes(loginbase)
		if len(allsitenodes) == 0:
			logger.info("Site has no nodes or not in DB")
			print "Site has no nodes or not in DB"
			return

		numnodes = len(allsitenodes)
		sicknodes = []
		# Get all sick nodes at this site
		up = 0
		down = 0
		for node in allsitenodes:

			nodename = node
			if nodename in self.act_all: # [nodename]:
				rec = self.act_all[nodename][0]
				if rec['stage'] != "steady-state":
					down += 1
				else:
					up += 1
			else:
				up += 1

		if up + down != numnodes:
			print "ERROR: %s total nodes up and down != %d" % (loginbase, numnodes)

		return up

#class Policy(Thread):

def main():
	print "policy.py is a module, not a script for running directly."

if __name__ == '__main__':
	import os
	import plc
	try:
		main()
	except KeyboardInterrupt:
		print "Killed.  Exitting."
		logger.info('Monitor Killed')
		os._exit(0)
