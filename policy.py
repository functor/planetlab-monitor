#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: policy.py,v 1.14 2007/06/29 12:42:22 soltesz Exp $
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
from config import config
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

class PLC: pass

class Policy(Thread):
	def __init__(self, comonthread, sickNoTicket, emailed):
		self.comon = comonthread

		# the hostname to loginbase mapping
		self.plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")

		# Actions taken on nodes.
		self.cache_all = soltesz.if_cached_else(1, "act_all", lambda : {})
		self.act_all= soltesz.if_cached_else(1, "act_all", lambda : {})

		# A dict of actions to specific functions. PICKLE doesnt' like lambdas.
		self.actions = {}
		self.actions['suspendslices'] = lambda hn: plc.suspendSlices(hn)
		self.actions['nocreate'] = lambda hn: plc.removeSliceCreation(hn); 
		self.actions['rins'] = lambda hn: plc.nodeBootState(hn, "rins")	
		self.actions['noop'] = lambda hn: hn

		self.bootcds = soltesz.dbLoad("bootcds")
		self.emailed = emailed # host - > (time of email, type of email)

		# all sick nodes w/o tickets
		# from thread 
		self.sickNoTicket = sickNoTicket


		# sick nodes with no tickets 
		# sickdb{loginbase: [{hostname1: [buckets]}, {...}]}
		self.sickdb = {}
		Thread.__init__(self)

	def mergePreviousActions(self):	
		"""
		look at the sick node_records as reported by comon, and then look at the
		node_records in act_all.  There are four cases:
		1) problem in comon but not in act_all
			this ok, b/c it just means it's a new problem
		2) problem in comon and in act_all
			we need to figure out the mis-match.  Did the problem get better
			or worse?  Reset the stage clock to 'initial', if it's better,
			continue if it's gotten worse.  Hard to make this judgement here, though.
		3) no problem in comon, problem in act_all
			this may mean that the node is operational again, or that monitor
			knows how to define a problem that comon does not.  For now, if
			comon does not report a problem, monitor obeys.  Ultimately,
			however, we want to catch problems that comon can't see.
		4) no problem in comon, no problem in act_all
			there won't be a record in either db, so there's no code.

		TODO: this is where back-offs will be acknowledged.  If the nodes get
		better, it should be possible to 're-enable' the site, or slice, etc.
		"""
		sorted_sites = self.sickdb.keys()
		sorted_sites.sort()
		# look at all problems reported by comon
		for loginbase in sorted_sites:
			rec_nodedict = self.sickdb[loginbase]
			sorted_nodes = rec_nodedict.keys()
			sorted_nodes.sort()
			#for rec_node in rec_nodelist:
			for nodename in sorted_nodes:
				rec_node = rec_nodedict[nodename]
				hn = nodename
				x = self.sickdb[loginbase][hn]
				if hn in self.act_all:
					y = self.act_all[hn][0]
					if x['bucket'][0] != y['bucket'][0]:
						# 2a) mismatch, need a policy for how to resolve
						print "COMON and MONITOR have a mismatch: %s vs %s" % \
							(x['bucket'], y['bucket'])
					else:
						# 2b) ok, b/c they agree that there's still a problem..
						pass

					# for now, overwrite the comon entry for the one in act_all
					self.sickdb[loginbase][hn] = y
					# delete the entry from cache_all to keep it out of case 3)
					del self.cache_all[hn]
				else:
					# 1) ok, b/c it's a new problem.
					pass

		# 3) nodes that remin in cache_all were not identified by comon as
		# 	down.  Do we keep them or not?
		for hn in self.cache_all.keys():
			y = self.act_all[hn][0]
			if 'monitor' in y['bucket']:
				loginbase = self.plcdb_hn2lb[hn] 
				if loginbase not in self.sickdb:
					self.sickdb[loginbase] = {}
				self.sickdb[loginbase][hn] = y
			else:
				del self.cache_all[hn]

		print "len of cache_all: %d" % len(self.cache_all.keys())

		return

	def accumSickSites(self):
		"""
		Take all sick nodes, find their sites, and put in 
		sickdb[loginbase] = [diag_node1, diag_node2, ...]
		"""
		while 1:
			diag_node = self.sickNoTicket.get(block = True)
			if diag_node == "None": 
				break

			#for bucket in self.comon.comon_buckets.keys():
			#	if (hostname in getattr(self.comon, bucket)):
			#		buckets_per_node.append(bucket)

			#########################################################
			# TODO: this will break with more than one comon bucket!!
			nodename = diag_node['nodename']
			loginbase = self.plcdb_hn2lb[nodename] # plc.siteId(node)

			if loginbase not in self.sickdb:
				self.sickdb[loginbase] = {}
				#self.sickdb[loginbase][nodename] = []
			#else:
				#if nodename not in self.sickdb[loginbase]:
				#	self.sickdb[loginbase][nodename] = []

			#self.sickdb[loginbase][nodename].append(diag_node)
			self.sickdb[loginbase][nodename] = diag_node
			# TODO: this will break with more than one comon bucket!!
			#########################################################


	def __actOnDebug(self, node):
		"""
		If in debug, set the node to rins, reboot via PCU/POD
		"""
		daysdown = self.comon.codata[node]['sshstatus'] // (60*60*24)
		logger.info("POLICY:  Node %s in dbg.  down for %s" %(node,daysdown))
		plc.nodeBootState(node, "rins")	
		# TODO: only reboot if BootCD > 3.0
		# if bootcd[node] > 3.0:
		#	if NODE_KEY in planet.cnf:
		#		plc.nodeBootState(node, "rins")	
		#		reboot.reboot(node)
		#	else:
		#		email to update planet.cnf file

		# If it has a PCU
		reboot.reboot(node)
		# else:
		#	email upgrade bootcd message, and treat as down.
		# Log it 
		self.actionlogdb[node] = ['rins', daysdown, time.time()] 

	def __emailSite(self, loginbase, roles, message, args):
		"""
		loginbase is the unique site abbreviation, prepended to slice names.
		roles contains TECH, PI, USER roles, and derive email aliases.
		record contains {'message': [<subj>,<body>], 'args': {...}} 
		"""
		args.update({'loginbase':loginbase})
		# build targets
		contacts = []
		if TECH & roles:
			contacts += [TECHEMAIL % loginbase]
		elif PI & roles:
			contacts += [PIEMAIL % loginbase]
		elif USER & roles:
			slices = plc.slices(loginbase)
			if len(slices) >= 1:
				for slice in slices:
					contacts += [SLICEMAIL % slice]
			else:
				print "Received no slices for site: %s" % loginbase

		try:
			subject = message[0] % args
			body = message[1] % args
			mailer.emailViaRT(subject, body, contacts)	
		except Exception, err:
			print "exception on message:"
			print message

		return

	def format_diaginfo(self, diag_node):
		info = diag_node['info']
		hlist = "    %s %s %s\n" % (info[0], info[2], info[1]) # (node, version, daysdown)
		return hlist

	def __actOnSite(self, loginbase, rec_diaglist):
		i_nodes_actedon = 0
		i_nodes_emailed = 0
		b_squeeze = config.squeeze

		action_argslist = []
		for diag_node in rec_diaglist:
			#print "calling actOnNode(%s)" % diag_node['nodename']
			action_args = self.__actOnNode(diag_node)
			action_argslist += [action_args]

		#print "getSiteNodes(%s)" % loginbase
		nodelist = plc.getSiteNodes(loginbase)
		if len(nodelist) - len(action_argslist) < 2:
			print "SITE: %20s : < 2 nodes !!" % loginbase
			# TODO: check how long this has occurred.
			# then plc.removeSliceCreation(nodename)
			# There may be a similar act_1,act_2,wait db for sites?
		else:
			#print "SITE: goodNodesUp(%s) > 2 && %d bad" % \
			#	(loginbase, len(action_argslist))
			b_squeeze = False

		# create 'args' for email
		#print "Create email args..."
		email_args = {}
		email_args['hostname_list'] = ""
		for action_args in action_argslist:
			email_args['hostname_list'] += action_args['msg_format']
			email_args['hostname'] = action_args['nodename']

		# Send email, perform node action
		# TODO: only send one email per site for a given problem...
		if len(action_argslist) > 0:
			action_args = action_argslist[0]
		#for action_args in action_argslist:
			# TODO: perform the most severe action?
			if b_squeeze:
				act_key = action_args['action']
				self.actions[act_key](email_args['hostname'])
				i_nodes_actedon += 1
			#print "Send email..."
			if action_args['message'] != None:
		 		self.__emailSite(loginbase, action_args['email'], 
							 action_args['message'], email_args)
				if config.mail: i_nodes_emailed += 1
		
		return (i_nodes_actedon, i_nodes_emailed)

	def __actOnNode(self, diag_node):
		nodename = diag_node['nodename']
		message = diag_node['message']
		info	= diag_node['info']
		args = {}

		# TODO: a node should only be in one category, right?
		# - This is a constraint that should be enforced.  It may be possible
		#   for a node to fall into the wrong set.
		# - Also, it is necessary to remove a node from an action set, if it
		#   comes back up, or enters another state between checks.
		# TODO: check that the reason a node ends up in a 'bad' state has or
		#   hasn't changed.  If it's changed, then probably the process should
		#   start over, or at leat be acknowledged.  I'm not sure that this is
		#   the right place for this operation.

		args['nodename'] = nodename
		args['msg_format'] = self.format_diaginfo(diag_node)
		current_time = time.time()

		#k1 = self.act_1week.keys()
		#k2 = self.act_2weeks.keys()
		#k3 = self.act_waitforever.keys()
		#print "lengths: %d %d %d" % (len(k1), len(k2), len(k3))

		delta = current_time - diag_node['time']

		if 'waitforever' in diag_node['stage']:
			# TODO: define what to do in the 'forever' state
			# TODO: there should probably be a periodic email sent after this,
			# 		to the site, or to us...
			args['action'] = 'noop'
			args['message'] = None

		elif 'actintwoweeks' in diag_node['stage'] or delta >= 14 * SPERDAY:
			#nodename in self.act_2weeks:
			args['email'] = TECH | PI | USER
			args['action'] = 'suspendslices'
			args['message'] = message[2]
			args['stage'] = 'stage_waitforever'
			# TODO: This will lose original 'time'
			diag_node.update(args)

		elif 'actinoneweek' in diag_node['stage'] or delta >= 7 * SPERDAY: 
			# nodename in self.act_1week:
			args['email'] = TECH | PI
				
			args['action'] = 'nocreate' 
			# args['action'] = 'rins'
			args['message'] = message[1]
			args['stage'] = 'stage_actintwoweeks'
			diag_node.update(args)

		else:
			# the node is bad, but there's no previous record of it.
			args['email'] = TECH
			args['action'] = 'noop'
			args['message'] = message[0]
			args['stage'] = 'stage_actinoneweek'
			diag_node.update(args)

		print "%s" % diag_node['log'],
		print "%15s" % args['action']

		if nodename not in self.act_all: self.act_all[nodename] = []
		self.act_all[nodename].insert(0,diag_node)

		return args
			
	def lappend_once(list, element):
		if element not in list:
			list.append(element)
	def sappend_once(string, element, separator=','):
		if element not in string:
			return ("%s%c%s" % (string, separator, element),1)
		else:
			return (string,0)

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
			rec_nodedict = self.sickdb[loginbase]
			#print "calling diagnoseSite(%s)" % loginbase
			rec_diaglist = self.__diagnoseSite(loginbase, rec_nodedict)
			l_allsites += [loginbase]
			

			if len(rec_diaglist) > 0:
				i_nodes_diagnosed += len(rec_diaglist)
				i_sites_diagnosed += 1

			#print "calling actOnSite(%s)" % loginbase
			(na,ne) = self.__actOnSite(loginbase, rec_diaglist)

			i_sites += 1
			i_nodes_actedon += na
			i_sites_emailed += ne

		return {'sites': i_sites, 
				'sites_diagnosed': i_sites_diagnosed, 
				'nodes_diagnosed': i_nodes_diagnosed, 
				'sites_emailed': i_sites_emailed, 
				'nodes_actedon': i_nodes_actedon, 
				'allsites':l_allsites}


	def __diagnoseSite(self, loginbase, rec_nodedict):
		"""
		rec_sitelist is a sickdb entry: 
		"""
		diag_list = []
		sorted_nodes = rec_nodedict.keys()
		sorted_nodes.sort()
		for nodename in sorted_nodes:
			rec_node = rec_nodedict[nodename]
			diag_node = self.__diagnoseNode(loginbase, rec_node)
			if diag_node != None:
				diag_list += [ diag_node ]
		return diag_list

	def __getDaysDown(self, nodename):
		daysdown = -1
		if self.comon.codata[nodename]['sshstatus'] != "null":
			daysdown = int(self.comon.codata[nodename]['sshstatus']) // (60*60*24)
		return daysdown

	def __getStrDaysDown(self, nodename):
		daysdown = self.__getDaysDown(nodename)
		if daysdown > 0:
			return "(%d days down)"%daysdown
		else:
			return ""

	def __getCDVersion(self, nodename):
		cdversion = ""
		if nodename in self.bootcds:
			cdversion = self.bootcds[nodename]
		return cdversion

	def __diagnoseNode(self, loginbase, rec_node):
		# TODO: change the format of the hostname in this 
		#		record to something more natural.
		nodename = rec_node['nodename']
		buckets = rec_node['bucket']
		diag_record = None

		# xyz as determined by monitor
		# down as determined by comon
		if rec_node['stage'] == "stage_rt_working":
			# err, this can be used as a counter of some kind..
			# but otherwise, no diagnosis is necessary, return None, implies that
			# it gets skipped.
			print "DIAG: %20s : %-40s ticket %s" % \
					(loginbase, nodename, rec_node['ticket_id'])
			
		elif   "down" in buckets:
			diag_record = {}
			diag_record.update(rec_node)
			diag_record['nodename'] = nodename
			diag_record['message'] = emailTxt.mailtxt.newdown
			diag_record['args'] = {'nodename': nodename}
			s_daysdown = self.__getStrDaysDown(nodename)
			diag_record['info'] = (nodename, s_daysdown, "")
			diag_record['bucket'] = ["down"]
			diag_record['log'] = "DOWN: %20s : %-40s == %20s" % \
					(loginbase, nodename, diag_record['info']),

		elif "dbg"  in buckets:
			# V2 boot cds as determined by monitor
			s_daysdown = self.__getStrDaysDown(nodename)
			s_cdversion = self.__getCDVersion(nodename)
			diag_record = {}
			diag_record.update(rec_node)
			diag_record['nodename'] = nodename
			diag_record['info'] = (nodename, s_daysdown, s_cdversion)

			if nodename in self.bootcds and "v2" in self.bootcds[nodename]:
				diag_record['log'] = "BTCD: %20s : %-40s == %20s" % \
					(loginbase, nodename, self.bootcds[nodename]),
				diag_record['message'] = emailTxt.mailtxt.newbootcd
				diag_record['args'] = {'nodename': nodename}
				# TODO: figure a better 'bucket' scheme, for merge()
				#diag_record['bucket'] = ["monitor"]
			else:
				print "DEBG: %20s : %-40s" % \
					(loginbase, nodename)
				return None

				msg = ("dbg mode", 
						"Comon reports the node in debug mode, %s" % \
						"but monitor does not know what to do yet.")
				# TODO: replace with a real action
				diag_record['message']  = [msg, msg, msg]
				diag_record['bucket'] = ["dbg"]
				diag_record['args'] = {'nodename': nodename}
		elif "ssh"    in buckets:
			pass
		elif "clock_drift"    in buckets:
			pass
		elif "dns"    in buckets:
			pass
		elif "filerw"    in buckets:
			pass
		else:
			print "Unknown buckets!!!! %s" % buckets
			sys.exit(1)

		return diag_record


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


	def __policy(self, node, loginbase, bucket):
		# ...and spam 'em
		target = [TECHEMAIL % loginbase]
		tmp = emailTxt.mailtxt.down
		sbj = tmp[0] % {'hostname': node}
		msg = tmp[1] % {'hostname': node, 'days': daysdown}
		mailer.email(sbj, msg, target)	


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
		for bucket in self.comon.comon_buckets.keys():
			for host in getattr(self.comon, bucket):
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
	
	def print_stats(self, key, stats):
		print "%20s : %d" % (key, stats[key])

	def run(self):
		self.accumSickSites()
		print "merge"
		self.mergePreviousActions()
		print "Accumulated %d sick sites" % len(self.sickdb.keys())
		logger.debug("Accumulated %d sick sites" % len(self.sickdb.keys()))

		#l1_before = len(self.act_1week.keys())
		#l2_before = len(self.act_2weeks.keys())
		#lwf_before = len(self.act_waitforever.keys())

		print "analyse"
		stats = self.analyseSites()
		print "DONE"

		self.print_stats("sites", stats)
		self.print_stats("sites_diagnosed", stats)
		self.print_stats("nodes_diagnosed", stats)
		self.print_stats("sites_emailed", stats)
		self.print_stats("nodes_actedon", stats)
		print string.join(stats['allsites'], ",")

		#l1 = len(self.act_1week.keys())
		#l2 = len(self.act_2weeks.keys())
		#lwf = len(self.act_waitforever.keys())
		#print "act_1week: %d diff: %d" % (l1, abs(l1-l1_before))
		#print "act_2weeks: %d diff: %d" % (l2, abs(l2-l2_before))
		#print "act_waitforever: %d diff: %d" % (lwf, abs(lwf-lwf_before))

		#self.__actOnDown()

		if config.policysavedb:
			print "Saving Databases... act_all"
			#soltesz.dbDump("policy.eventlog", self.eventlog)
			soltesz.dbDump("act_all", self.act_all)



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
