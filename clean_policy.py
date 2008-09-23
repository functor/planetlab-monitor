import config
import database 
import time
import mailer
from unified_model import cmpCategoryVal
import sys
import emailTxt
import string

from rt import is_host_in_rt_tickets
import plc

# Time to enforce policy
POLSLEEP = 7200

# Where to email the summary
SUMTO = "soltesz@cs.princeton.edu"

from const import *

from unified_model import *

def get_ticket_id(record):
	if 'ticket_id' in record and record['ticket_id'] is not "" and record['ticket_id'] is not None:
		return record['ticket_id']
	elif 		'found_rt_ticket' in record and \
		 record['found_rt_ticket'] is not "" and \
		 record['found_rt_ticket'] is not None:
		return record['found_rt_ticket']
	else:
		return None

class MonitorMergeDiagnoseSendEscellate:
	act_all = None
	fb = None

	def __init__(self, hostname, act):
		self.hostname = hostname
		self.act = act
		self.plcdb_hn2lb = None
		if self.plcdb_hn2lb is None:
			self.plcdb_hn2lb = database.dbLoad("plcdb_hn2lb")
		self.loginbase = self.plcdb_hn2lb[self.hostname]
		return

	def getFBRecord(self):
		if MonitorMergeDiagnoseSendEscellate.fb == None:
			MonitorMergeDiagnoseSendEscellate.fb = database.dbLoad("findbad")

		fb = MonitorMergeDiagnoseSendEscellate.fb

		if self.hostname in fb['nodes']:
			fbnode = fb['nodes'][self.hostname]['values']
		else:
			raise Exception("Hostname %s not in scan database"% self.hostname)
		return fbnode

	def getActionRecord(self):
		# update ticket status
		if MonitorMergeDiagnoseSendEscellate.act_all == None:
			MonitorMergeDiagnoseSendEscellate.act_all = database.dbLoad("act_all")

		act_all = MonitorMergeDiagnoseSendEscellate.act_all 

		if self.hostname in act_all and len(act_all[self.hostname]) > 0:
			actnode = act_all[self.hostname][0]
		else:
			actnode = None
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
		fbnode['email'] = TECH
		fbnode['action-level'] = 0
		fbnode['action'] = ['noop']
		fbnode['date_created'] = time.time()

		if actnode is None: # there is no entry in act_all
			actnode = {} 
			actnode.update(fbnode)
			actnode['ticket_id'] = ""
			actnode['prev_category'] = "ERROR" 
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
		#diag.setFlag('ResetStage')
		if record.stageIswaitforever():
			ticket = record.data['rt']
			if 'new' in ticket['Status']:
				print "Resetting Stage!!!!!"
			#	diag.setFlag('ResetStage')
				record.reset_stage()
			#if diag.getFlag('ResetStage'):
			#	print "diagnose: resetting stage"
			#	diag.resetFlag('ResetStage')
				
			if 'resolved' in ticket['Status']:
				diag.setFlag('RTEndRecord')

		# NOTE: take category, and prepare action
		category = record.getCategory()
		if category == "error":
			diag.setFlag('SendNodedown')
			record.data['message_series'] = emailTxt.mailtxt.newdown
			record.data['log'] = self.getDownLog(record)

		elif category == "prod" or category == "alpha":
			state = record.getState()
			if state == "boot":
				if record.severity() != 0:
					diag.setFlag('SendThankyou')
					print "RESETTING STAGE: improvement"
					record.data['stage'] = 'improvement'
					record.data['message_series'] = emailTxt.mailtxt.newthankyou
					record.data['log'] = self.getThankyouLog(record)
				else:
					# NOTE: do nothing, since we've already done the above.
					print "DIAGNOSED: %s is boot. no further action necessary." % record.hostname
					return None
			elif state == "debug":
				pass
			else:
				print "unknown state %s for host %s" % (state, self.hostname)
		else:
			print "unknown category: %s" % category


		# TODO: how to not send email?...
		record = self.checkStageAndTime(diag,record)
		#if record:
		print "diagnose: checkStageAndTime Returned Valid Record"
		site = PersistFlags(self.loginbase, 1, db='site_persistflags')

		if "good" not in site.status: #  != "good":
			print "diagnose: Setting site %s for 'squeeze'" % self.loginbase
			diag.setFlag('Squeeze')
		else:
			print "diagnose: Setting site %s for 'backoff'" % self.loginbase
			diag.setFlag('BackOff')

		diag.save()
		return diag
		#else:
		#	print "checkStageAndTime Returned NULL Record"
		#	return None

	def action(self, record, diag):

		message = None

		#print record.data['stage']
		#print "improvement" in record.data['stage']
		#print self.getSendEmailFlag(record)
		print "%s %s DAYS DOWN" % ( self.hostname, Record.getDaysDown(record.data) )
		if ( self.getSendEmailFlag(record) and Record.getDaysDown(record.data) >= 2 ) or \
			"monitor-end-record" in record.data['stage']:
			print "action: getting message"
			message = record.getMessage(record.data['ticket_id'])
			if message:
				#message.reset()
				print "action: sending email"
				message.send(record.getContacts())
				#print "DEBUG NOT SENDING MESSAGE WHEN I SHOULD BE!!!!!"
				#print "DEBUG NOT SENDING MESSAGE WHEN I SHOULD BE!!!!!"
				#print "DEBUG NOT SENDING MESSAGE WHEN I SHOULD BE!!!!!"
				#print message
				if message.rt.ticket_id:
					print "action: setting record ticket_id"
					record.data['ticket_id'] = message.rt.ticket_id

			if ( record.data['takeaction'] and diag.getFlag('Squeeze') ): 
				print "action: taking action"
				record.takeAction(record.data['action-level'])
				diag.resetFlag('Squeeze')
				diag.save()
			if diag.getFlag('BackOff'):
				record.takeAction(0)
				diag.resetFlag('BackOff')
				diag.save()

			if record.saveAction():
				print "action: saving act_all db"
				self.add_and_save_act_all(record)
			else:
				print "action: NOT saving act_all db"
				print "stage: %s %s" % ( record.data['stage'], record.data['save-act-all'] )

			if record.improved() or diag.getFlag('RTEndRecord'):
				print "action: end record for %s" % self.hostname
				record.end_record()
				diag.setFlag('CloseRT')
				diag.resetFlag('RTEndRecord')
				diag.save()
				#return None

			if message:
				if diag.getFlag('CloseRT'):
					message.rt.closeTicket()
					diag.resetFlag('CloseRT')
					diag.save()

		else:
			print "NOT sending email : %s %s" % (config.mail, record.data['rt'])

		return

	def getSendEmailFlag(self, record):
		if not config.mail:
			return False

		# resend if open & created longer than 30 days ago.
		if  'rt' in record.data and \
			'Status' in record.data['rt'] and \
			"open" in record.data['rt']['Status'] and \
			record.data['rt']['Created'] > int(time.time() - 60*60*24*30):
			# if created-time is greater than the thirty days ago from the current time
			return False

		return True

	def add_and_save_act_all(self, record):
		self.act_all = database.dbLoad("act_all")
		if self.hostname not in self.act_all:
			self.act_all[self.hostname] = []
		self.act_all[self.hostname].insert(0,record.data)
		database.dbDump("act_all", self.act_all)
		
	def getDownLog(self, record):

		record.data['args'] = {'nodename': self.hostname}
		record.data['info'] = (self.hostname, Record.getStrDaysDown(record.data), "")

		#for key in record.data.keys():
		#	print "%10s %s %s " % (key, "==", record.data[key])

		if record.data['ticket_id'] == "" and 'found_rt_ticket' in record.data:
			log = "DOWN: %20s : %-40s == %20s %s" % \
				(self.loginbase, self.hostname, record.data['info'][1:], record.data['found_rt_ticket'])
		else:
			log = "DOWN: %20s : %-40s == %20s %s" % \
				(self.loginbase, self.hostname, record.data['info'][1:], record.data['ticket_id'])
		return log

	def getThankyouLog(self, record):

		record.data['args'] = {'nodename': self.hostname}
		record.data['info'] = (self.hostname, record.data['prev_category'], record.data['category'])

		try:
			if record.data['ticket_id'] == "" and 'found_rt_ticket' in record.data:
				log = "IMPR: %20s : %-40s == %20s %20s %s %s" % \
						(self.loginbase, self.hostname, record.data['stage'], 
						 record.data['prev_category'], record.data['category'], record.data['found_rt_ticket'])
			else:
				log = "IMPR: %20s : %-40s == %20s %20s %s %s" % \
						(self.loginbase, self.hostname, record.data['stage'], 
						 record.data['prev_category'], record.data['category'], record.data['ticket_id'])
		except:
			log = "IMPR: %s improved to %s " % (self.hostname, record.data['category'])
		return log

	def checkStageAndTime(self, diag, record):
		current_time = time.time()
		delta = current_time - record.data['time']
		#print record.data
		if   'findbad' in record.data['stage']:
			# The node is bad, and there's no previous record of it.
			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['takeaction'] = False
			record.data['message'] = record.data['message_series'][0]
			record.data['stage'] = 'stage_actinoneweek'
			record.data['save-act-all'] = True
			record.data['action-level'] = 0

		elif 'reboot_node' in record.data['stage']:
			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['message'] = record.data['message_series'][0]
			record.data['stage'] = 'stage_actinoneweek'
			record.data['takeaction'] = False
			record.data['save-act-all'] = False
			record.data['action-level'] = 0
			
		elif 'improvement' in record.data['stage']:
			print "checkStageAndTime: backing off of %s" % self.hostname
			record.data['action'] = ['close_rt']
			record.data['takeaction'] = True
			record.data['message'] = record.data['message_series'][0]
			record.data['stage'] = 'monitor-end-record'
			record.data['save-act-all'] = True
			record.data['action-level'] = 0

		elif 'actinoneweek' in record.data['stage']:
			if delta >= 7 * SPERDAY: 
				print "checkStageAndTime: transition to next stage actintwoweeks"
				record.data['email'] = TECH | PI
				record.data['stage'] = 'stage_actintwoweeks'
				record.data['message'] = record.data['message_series'][1]
				record.data['action'] = ['nocreate' ]
				record.data['time'] = current_time		# reset clock for waitforever
				record.data['takeaction'] = True
				record.data['save-act-all'] = True
				record.data['action-level'] = 1
			elif delta >= 3* SPERDAY and not 'second-mail-at-oneweek' in record.data:
				print "checkStageAndTime: second message in one week"
				record.data['email'] = TECH 
				record.data['message'] = record.data['message_series'][0]
				record.data['action'] = ['sendmailagain-waitforoneweekaction' ]
				record.data['second-mail-at-oneweek'] = True
				record.data['takeaction'] = False
				record.data['save-act-all'] = True
				record.data['action-level'] = 0
			else:
				record.data['message'] = None
				record.data['action'] = ['waitforoneweekaction' ]
				record.data['takeaction'] = False
				record.data['save-act-all'] = False
				record.data['action-level'] = 0
				print "checkStageAndTime: ignoring this record for: %s" % self.hostname
				#return None 			# don't send if there's no action

		elif 'actintwoweeks' in record.data['stage']:
			if delta >= 7 * SPERDAY:
				print "checkStageAndTime: transition to next stage waitforever"
				record.data['email'] = TECH | PI | USER
				record.data['stage'] = 'stage_waitforever'
				record.data['message'] = record.data['message_series'][2]
				record.data['action'] = ['suspendslices']
				record.data['time'] = current_time		# reset clock for waitforever
				record.data['takeaction'] = True
				record.data['save-act-all'] = True
				record.data['action-level'] = 2
			elif delta >= 3* SPERDAY and not 'second-mail-at-twoweeks' in record.data:
				print "checkStageAndTime: second message in one week for stage two"
				record.data['email'] = TECH | PI
				record.data['message'] = record.data['message_series'][1]
				record.data['action'] = ['sendmailagain-waitfortwoweeksaction' ]
				record.data['second-mail-at-twoweeks'] = True
				record.data['takeaction'] = False
				record.data['save-act-all'] = True
				record.data['action-level'] = 1
			else:
				record.data['message'] = None
				record.data['takeaction'] = False
				record.data['action'] = ['waitfortwoweeksaction']
				record.data['save-act-all'] = False
				print "checkStageAndTime: second message in one week for stage two"
				record.data['action-level'] = 1
				#return None 			# don't send if there's no action

		elif 'ticket_waitforever' in record.data['stage']:
			record.data['email'] = TECH
			record.data['takeaction'] = True
			if 'first-found' not in record.data:
				record.data['first-found'] = True
				record.data['log'] += " firstfound"
				record.data['action'] = ['ticket_waitforever']
				record.data['message'] = None
				record.data['time'] = current_time
				record.data['save-act-all'] = True
				record.data['action-level'] = 2
			else:
				if delta >= 7*SPERDAY:
					record.data['action'] = ['ticket_waitforever']
					record.data['message'] = None
					record.data['time'] = current_time		# reset clock
					record.data['save-act-all'] = True
					record.data['action-level'] = 2
				else:
					record.data['action'] = ['ticket_waitforever']
					record.data['message'] = None
					record.data['takeaction'] = False
					record.data['save-act-all'] = False
					record.data['action-level'] = 2
					#return None

		elif 'waitforever' in record.data['stage']:
			# more than 3 days since last action
			# TODO: send only on weekdays.
			# NOTE: expects that 'time' has been reset before entering waitforever stage
			record.data['takeaction'] = True
			if delta >= 3*SPERDAY:
				record.data['action'] = ['email-againwaitforever']
				record.data['message'] = record.data['message_series'][2]
				record.data['time'] = current_time		# reset clock
				record.data['save-act-all'] = True
				record.data['action-level'] = 2
			else:
				record.data['action'] = ['waitforever']
				record.data['message'] = None
				record.data['takeaction'] = False
				record.data['save-act-all'] = False
				record.data['action-level'] = 2
				#return None 			# don't send if there's no action

		else:
			# There is no action to be taken, possibly b/c the stage has
			# already been performed, but diagnose picked it up again.
			# two cases, 
			#	1. stage is unknown, or 
			#	2. delta is not big enough to bump it to the next stage.
			# TODO: figure out which. for now assume 2.
			print "UNKNOWN stage for %s; nothing done" % self.hostname
			record.data['action'] = ['unknown']
			record.data['message'] = record.data['message_series'][0]

			record.data['email'] = TECH
			record.data['action'] = ['noop']
			record.data['message'] = record.data['message_series'][0]
			record.data['stage'] = 'stage_actinoneweek'
			record.data['time'] = current_time		# reset clock
			record.data['takeaction'] = False
			record.data['save-act-all'] = True

		print "%s" % record.data['log'],
		print "%15s" % record.data['action']
		return record
		
