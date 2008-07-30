from config import config
#print "policy"
config = config()
import soltesz
import time
import mailer
from www.printbadnodes import cmpCategoryVal
import sys
import emailTxt
import string

from policy import get_ticket_id, print_stats, close_rt_backoff, reboot_node
from rt import is_host_in_rt_tickets
import plc

# Time to enforce policy
POLSLEEP = 7200

# Where to email the summary
SUMTO = "soltesz@cs.princeton.edu"

from const import *

from unified_model import *

class MonitorMergeDiagnoseSendEscellate:
	def __init__(self, hostname, act):
		self.hostname = hostname
		self.act = act
		self.plcdb_hn2lb = None
		if self.plcdb_hn2lb is None:
			self.plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")
		self.loginbase = self.plcdb_hn2lb[self.hostname]
		return

	def getFBRecord(self):
		fb = soltesz.dbLoad("findbad")
		if self.hostname in fb['nodes']:
			fbnode = fb['nodes'][self.hostname]['values']
		else:
			raise Exception("Hostname %s not in scan database"% self.hostname)
		return fbnode

	def getActionRecord(self):
		# update ticket status
		act_all = soltesz.dbLoad("act_all")
		if self.hostname in act_all and len(act_all[self.hostname]) > 0:
			actnode = act_all[self.hostname][0]
		else:
			actnode = None
		del act_all
		return actnode

	def getKernel(self, unamestr):
		s = unamestr.split()
		if len(s) > 2:
			return s[2]
		else:
			return ""

	def mergeRecord(self, fbnode, actnode):
		fbnode['kernel'] = self.getKernel(fbnode['kernel'])
		fbnode['stage'] = "findbad"
		fbnode['message'] = None
		fbnode['args'] = None
		fbnode['info'] = None
		fbnode['log'] = None
		fbnode['time'] = time.time()
		fbnode['date_created'] = time.time()

		if actnode is None:
			actnode = {} 
			actnode.update(fbnode)
			actnode['ticket_id'] = ""
			actnode['prev_category'] = "NORECORD" 
		else:
			actnode['prev_category']= actnode['category']
			actnode['comonstats']	= fbnode['comonstats']
			actnode['category']		= fbnode['category']
			actnode['state'] 		= fbnode['state']
			actnode['kernel']		= fbnode['kernel']
			actnode['bootcd']		= fbnode['bootcd']
			actnode['plcnode']		= fbnode['plcnode']
			ticket = get_ticket_id(actnode)
			if ticket is None: actnode['ticket_id'] = ""
			actnode['rt'] = mailer.getTicketStatus(ticket)

			#for key in actnode.keys():
			#	print "%10s %s %s " % (key, "==", actnode[key])
			#print "----------------------------"

		return actnode

	def run(self):
		fbnode = self.getFBRecord()
		actnode= self.getActionRecord()
		actrec = self.mergeRecord(fbnode, actnode)
		record = Record(self.hostname, actrec)
		diag   = self.diagnose(record)
		if self.act and diag is not None:
			self.action(record,diag)
	
	def diagnose(self, record):

		diag = PersistFlags(record.hostname, 60*60*24, db='persist_diagnose_flags')
		# NOTE: change record stage based on RT status.
		diag.setFlag('ResetStage')
		if record.stageIswaitforever():
			ticket = record.data['rt']
			if 'new' in ticket['Status']:
				diag.setFlag('ResetStage')
				
			if 'resolved' in ticket['Status']:
				diag.setFlag('EndRecord')

		# NOTE: take category, and prepare action
		category = record.getCategory()
		if category == "error":
			diag.setFlag('SendNodedown')
			record.data['message'] = emailTxt.mailtxt.newdown
			record.data['log'] = self.getDownLog(record)

		elif category == "prod":
			state = diag.getState()
			if state == "boot":
				diag.setFlag('SendThankyou')
				record.data['message'] = emailTxt.mailtxt.newthankyou
				record.data['log'] = self.getThankyouLog(record)

			elif state == "debug":
				pass
			else:
				print "unknown state %s for host %s" % (state, self.hostname)
		else:
			print "unknown category: %s" % category

		if diag.getFlag('ResetStage'):
			print "resetting stage"
			record.reset_stage()

		record = self.checkStageAndTime(diag,record)
		if record:
			print "checkStageAndTime Returned Valid Record"
			site = PersistFlags(self.loginbase, 1, db='site_persistflags')

			if site.status is not "good":
				print "Setting site %s for 'squeeze'" % self.loginbase
				diag.setFlag('Squeeze')
			else:
				print "Setting site %s for 'backoff'" % self.loginbase
				diag.setFlag('BackOff')

			diag.save()
			return diag
		else:
			print "checkStageAndTime Returned NULL Record"
			return None

	def action(self, record, diag):
		if record.improved() or diag.getFlag('EndRecord'):
			print "end record for %s" % self.hostname
			record.end_record()
			diag.setFlag('CloseRT')
			return None

		if self.getSendEmailFlag(record): 
			print "sending email"
			message = record.getMessage(record.data['ticket_id'])
			message.reset()
			message.send(record.getContacts())
			if message.rt.ticket_id:
				print "setting record ticket_id"
				record.data['ticket_id'] = message.rt.ticket_id
			if diag.getFlag('CloseRT'):
				message.rt.closeTicket()
		else:
			print "NOT sending email : %s %s" % (config.mail, record.data['rt'])

		if record.data['takeaction'] and diag.getFlag('Squeeze'):
			print "taking action"
			record.takeAction()

		print "saving act_all db"
		self.add_and_save_act_all(record)

		return

	def getSendEmailFlag(self, record):
		if not config.mail:
			return False

		# resend if open & created longer than 30 days ago.
		if  'rt' in record.data and \
			'Status' in record.data['rt'] and \
			"open" in record.data['rt']['Status'] and \
			record.data['rt']['Created'] < 60*60*24*30:
			return False

		return True

	def add_and_save_act_all(self, record):
		self.act_all = soltesz.dbLoad("act_all")
		self.act_all[self.hostname].insert(0,record.data)
		soltesz.dbDump("act_all", self.act_all)
		
	def getDownLog(self, record):

		record.data['args'] = {'nodename': self.hostname}
		record.data['info'] = (self.hostname, Record.getStrDaysDown(record.data), "")

		#for key in record.data.keys():
		#	print "%10s %s %s " % (key, "==", record.data[key])

		if record.data['ticket_id'] == "":
			log = "DOWN: %20s : %-40s == %20s %s" % \
				(self.loginbase, self.hostname, record.data['info'][1:], record.data['found_rt_ticket'])
		else:
			log = "DOWN: %20s : %-40s == %20s %s" % \
				(self.loginbase, self.hostname, record.data['info'][1:], record.data['ticket_id'])
		return log

	def getThankyouLog(self, record):

		record.data['args'] = {'nodename': self.hostname}
		record.data['info'] = (self.hostname, record.data['prev_category'], record.data['category'])

		if record.data['ticket_id'] == "":
			log = "IMPR: %20s : %-40s == %20s %20s %s %s" % \
						(self.loginbase, self.hostname, record.data['stage'], 
						 state, category, record.data['found_rt_ticket'])
		else:
			log = "IMPR: %20s : %-40s == %20s %20s %s %s" % \
						(self.loginbase, self.hostname, record.data['stage'], 
						 state, category, record.data['ticket_id'])
		return log

	def checkStageAndTime(self, diag, record):
		current_time = time.time()
		delta = current_time - record.data['time']
		if   'findbad' in record.data['stage']:
			# The node is bad, and there's no previous record of it.
			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['takeaction'] = False
			record.data['message'] = record.data['message'][0]
			record.data['stage'] = 'stage_actinoneweek'

		elif 'reboot_node' in record.data['stage']:
			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['message'] = record.data['message'][0]
			record.data['stage'] = 'stage_actinoneweek'
			record.data['takeaction'] = False
			
		elif 'improvement' in record.data['stage']:
			print "backing off of %s" % self.hostname
			record.data['action'] = ['close_rt']
			record.data['takeaction'] = True
			record.data['message'] = record.data['message'][0]
			record.data['stage'] = 'monitor-end-record'

		elif 'actinoneweek' in record.data['stage']:
			if delta >= 7 * SPERDAY: 
				record.data['email'] = TECH | PI
				record.data['stage'] = 'stage_actintwoweeks'
				record.data['message'] = record.data['message'][1]
				record.data['action'] = ['nocreate' ]
				record.data['time'] = current_time		# reset clock for waitforever
				record.data['takeaction'] = True
			elif delta >= 3* SPERDAY and not 'second-mail-at-oneweek' in record.data:
				record.data['email'] = TECH 
				record.data['message'] = record.data['message'][0]
				record.data['action'] = ['sendmailagain-waitforoneweekaction' ]
				record.data['second-mail-at-oneweek'] = True
				record.data['takeaction'] = False
			else:
				record.data['message'] = None
				record.data['action'] = ['waitforoneweekaction' ]
				print "ignoring this record for: %s" % self.hostname
				return None 			# don't send if there's no action

		elif 'actintwoweeks' in record.data['stage']:
			if delta >= 7 * SPERDAY:
				record.data['email'] = TECH | PI | USER
				record.data['stage'] = 'stage_waitforever'
				record.data['message'] = record.data['message'][2]
				record.data['action'] = ['suspendslices']
				record.data['time'] = current_time		# reset clock for waitforever
				record.data['takeaction'] = True
			elif delta >= 3* SPERDAY and not 'second-mail-at-twoweeks' in record.data:
				record.data['email'] = TECH | PI
				record.data['message'] = record.data['message'][1]
				record.data['action'] = ['sendmailagain-waitfortwoweeksaction' ]
				record.data['second-mail-at-twoweeks'] = True
				record.data['takeaction'] = False
			else:
				record.data['message'] = None
				record.data['action'] = ['waitfortwoweeksaction']
				return None 			# don't send if there's no action

		elif 'ticket_waitforever' in record.data['stage']:
			record.data['email'] = TECH
			record.data['takeaction'] = True
			if 'first-found' not in record.data:
				record.data['first-found'] = True
				record.data['log'] += " firstfound"
				record.data['action'] = ['ticket_waitforever']
				record.data['message'] = None
				record.data['time'] = current_time
			else:
				if delta >= 7*SPERDAY:
					record.data['action'] = ['ticket_waitforever']
					record.data['message'] = None
					record.data['time'] = current_time		# reset clock
				else:
					record.data['action'] = ['ticket_waitforever']
					record.data['message'] = None
					return None

		elif 'waitforever' in record.data['stage']:
			# more than 3 days since last action
			# TODO: send only on weekdays.
			# NOTE: expects that 'time' has been reset before entering waitforever stage
			record.data['takeaction'] = True
			if delta >= 3*SPERDAY:
				record.data['action'] = ['email-againwaitforever']
				record.data['message'] = record.data['message'][2]
				record.data['time'] = current_time		# reset clock
			else:
				record.data['action'] = ['waitforever']
				record.data['message'] = None
				return None 			# don't send if there's no action

		else:
			# There is no action to be taken, possibly b/c the stage has
			# already been performed, but diagnose picked it up again.
			# two cases, 
			#	1. stage is unknown, or 
			#	2. delta is not big enough to bump it to the next stage.
			# TODO: figure out which. for now assume 2.
			print "UNKNOWN stage for %s; nothing done" % self.hostname
			record.data['action'] = ['unknown']
			record.data['message'] = record.data['message'][0]

			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['message'] = record.data['message'][0]
			record.data['stage'] = 'stage_actinoneweek'
			record.data['time'] = current_time		# reset clock
			record.data['takeaction'] = False

		print "%s" % record.data['log'],
		print "%15s" % record.data['action']
		return record
		
