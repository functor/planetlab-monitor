import config
import database 
import time
import mailer
import sys
import emailTxt
import string
from monitor.wrapper import plccache
from datetime import datetime

from rt import is_host_in_rt_tickets
import plc

# Time to enforce policy
POLSLEEP = 7200

# Where to email the summary
SUMTO = "soltesz@cs.princeton.edu"

from const import *

from unified_model import *

class MonitorMergeDiagnoseSendEscellate:
	act_all = None

	def __init__(self, hostname, act):
		self.hostname = hostname
		self.act = act
		self.plcdb_hn2lb = None
		if self.plcdb_hn2lb is None:
			self.plcdb_hn2lb = plccache.plcdb_hn2lb 
		self.loginbase = self.plcdb_hn2lb[self.hostname]
		return

	def getFBRecords(self):
		fbrecs = FindbadNodeRecord.get_latest_n_by(hostname=self.hostname)
		fbnodes = None
		if fbrec: 
			fbnodes = fbrecs
		else:
			fbnodes = None
		return fbnodes

	def getLastActionRecord(self):
		actrec = ActionRecord.get_latest_by(hostname=self.hostname)
		actnode = None
		if actrec:
			actnode = actrec
		else:
			actnode = None
		return actnode

	def getPreviousCategory(self, actrec):
		ret = None
		if actrec:
			ret = actrec.findbad_records[0].observed_category
		else:
			ret = "ERROR"
		return ret


	def mergeRecord(self, fbnodes, actrec):

		actdefault = {}
		actdefault['date_created'] = datetime.now()
		actdefault['date_action_taken'] = datetime.now()

		actdefault['stage'] = "initial"
		actdefault['message_series'] = None
		actdefault['message_index'] = None
		actdefault['message_arguments'] = None

		actdefault['send_email_to'] = TECH
		actdefault['penalty_level'] = 0
		actdefault['action'] = [ 'noop' ]
		actdefault['take_action'] = False

		actdefault['ticket_id'] = ""
		actdefault['findbad_records'] = fbnodes
		actdefault['last_action_record'] = actrec

		actdefault['prev_category'] = self.getPreviousCategory(actrec)
		actdefault['category']		= fbnodes[0].observed_category

		actdefault['rt'] = mailer.getTicketStatus(actrec.ticket_id)

		return actdefault

	def run(self):
		fbnodes = self.getFBRecords()
		actnode= self.getLastActionRecord()
		actrec = self.mergeRecord(fbnodes, actnode)
		record = Record(self.hostname, actrec)
		diag   = self.diagnose(record)
		if self.act and diag is not None:
			self.action(record,diag)
	
	def diagnose(self, record):

		diag = {}
		# NOTE: change record stage based on RT status.
		if record.stageIswaitforever():
			ticket = record.data['rt']
			if 'new' in ticket['Status']:
				print "Resetting Stage!!!!!"
				record.reset_stage()
				
			if 'resolved' in ticket['Status']:
				diag['RTEndRecord'] = True

		# NOTE: take category, and prepare action
		category = record.getCategory()
		if category == "error":
			diag['SendNodedown'] = True
			record.data['message_series'] = emailTxt.mailtxt.newdown
			record.data['log'] = self.getDownLog(record)

		elif category == "prod" or category == "alpha":
			state = record.getState()
			if state == "boot":
				if record.severity() != 0:
					diag['SendThankyou'] = True
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
		record = self.checkStageAndTime(record)
		#if record:
		print "diagnose: checkStageAndTime Returned Valid Record"
		siterec = HistorySiteRecord.by_loginbase(self.loginbase)

		if "good" not in siterec.status: #  != "good":
			print "diagnose: Setting site %s for 'squeeze'" % self.loginbase
			diag['Squeeze'] = True
		else:
			print "diagnose: Setting site %s for 'backoff'" % self.loginbase
			diag['BackOff'] = True

		return diag

	def action(self, record, diag):

		message = None

		print "%s %s DAYS DOWN" % ( self.hostname, Record.getDaysDown(record.data) )
		if ( self.getSendEmailFlag(record) and Record.getDaysDown(record.data) >= 2 ) or \
			"monitor-end-record" in record.data['stage']:
			print "action: getting message"
			#### Send EMAIL
			message = record.getMessage(record.data['ticket_id'])
			if message:
				print "action: sending email"
				message.send(record.getContacts())
				if message.rt.ticket_id:
					print "action: setting record ticket_id"
					record.data['ticket_id'] = message.rt.ticket_id

			#### APPLY PENALTY
			if ( record.data['take_action'] and diag['Squeeze'] ): 
				print "action: taking action"
				record.takeAction(record.data['penalty_level'])
				del diag['Squeeze']
			if diag.getFlag('BackOff'):
				record.takeAction(0)
				del diag['BackOff']

			#### SAVE TO DB
			if record.saveAction():
				print "action: saving act_all db"
				self.add_and_save_act_all(record)
			else:
				print "action: NOT saving act_all db"
				print "stage: %s %s" % ( record.data['stage'], record.data['save_act_all'] )

			#### END RECORD
			if record.improved() or diag['RTEndRecord']:
				print "action: end record for %s" % self.hostname
				record.end_record()
				diag['CloseRT'] = True
				del diag['RTEndRecord']

			#### CLOSE RT TICKET
			if message:
				if diag['CloseRT']:
					message.rt.closeTicket()
					del diag['CloseRT']

		else:
			print "NOT sending email : %s" % config.mail

		return

	def add_and_save_act_all(self, record):
		"""
			Read the sync record for this node, and increment the round and
			create an ActionRecord for this host using the record.data values.
		"""
		recsync = RecordActionSync.get_by(hostname=self.hostname)
		rec = RecordAction(hostname=self.hostname)
		recsync.round += 1
		record.data['round'] = recsync.round
		# TODO: we will need to delete some of these before setting them in the DB.
		rec.set(**record.data)
		rec.flush()

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

	def makeRecord(self, **kwargs):
		rec = {}
		for key in kwargs.keys():
			rec[key] = kwargs[key]
		return rec

	def checkStageAndTime(self, record):
	"""
		The core variables are:

			send_email_to  : defines who to send messages to at this time
			take_action    : whether or not to take action
			penalty_level  : how much of a penalty to apply
			message_index  : where in the escellation sequence we are.
			save_act_all   : whether or not to save the action record in the db.

			action/stage   : stage tracks which state we're in.
	"""
		stages = {
			"initial"		: [ { action='noop', next="weekone"}],
			"weekone"		: [ { action='noop',         index=0, save=True, email=TECH,         length=7*SPERDAY,  next="weektwo" }, ],
			"weektwo"		: [ { action='nocreate',     index=1, save=True, email=TECH|PI,      length=7*SPERDAY,  next="waitforever" }, ],
			"waitforever"	: [ { action='suspendslices',index=2, save=True, email=TECH|PI|USER, length=7*SPERDAY,  next="waitforever" }, ],
			"paused"		: [ { action='noop', 				  save=True						 length=30*SPERDAY, next="weekone" }, ]
			"improvement"	: [ { action='close_rt',     index=0, save=True, email=TECH,         next="monitor-end-record" }, ],
		}
		# TODO: make this time relative to the PREVIOUS action taken.
		current_time = time.time()
		current_stage = record.getMostRecentStage()
		recent_time   = record.getMostRecentTime()

		delta = current_time - recent_time

		if current_stage in stages:
			values = stages[current_stage][0]

		if delta >= values['length']:
			print "checkStageAndTime: transition to next stage"
			new_stage = values['next']
			values = stages[new_stage]

		elif delta >= values['length']/3 and not 'second_mail_at_oneweek' in record.data:
			print "checkStageAndTime: second message in one week for stage two"
			take_action=False
			pass
		else:
			# DO NOTHING
			take_action=False, 
			save_act_all=False, 
			message_index=None, 
			print "checkStageAndTime: second message in one week for stage two"

		rec = self.makeRecord( stage=new_stage, send_email_to=values['email'],
							   action=values['action'], message_index=values['index'], 
							   save_act_all=values['save'], penalty_level=values['index'], 
							   date_action_taken=current_time)
		record.data.update(rec)


		if   'initial' in record.data['stage']:
			# The node is bad, and there's no previous record of it.
			rec = self.makeRecord(
							stage="weekone", send_email_to=TECH, 
							action=['noop'], take_action=False, 
							message_index=0, save_act_all=True, 
							penalty_level=0, )
			record.data.update(rec)

		elif 'improvement' in record.data['stage']:
			print "checkStageAndTime: backing off of %s" % self.hostname
			rec = self.makeRecord(
							stage='monitor-end-record', send_email_to=TECH, 
							action=['close_rt'], take_action=True, 
							message_index=0, save_act_all=True, 
							penalty_level=0, )
			record.data.update(rec)

		else:
			# There is no action to be taken, possibly b/c the stage has
			# already been performed, but diagnose picked it up again.
			# two cases, 
			#	1. stage is unknown, or 
			#	2. delta is not big enough to bump it to the next stage.
			# TODO: figure out which. for now assume 2.
			print "UNKNOWN stage for %s; nothing done" % self.hostname
			rec = self.makeRecord(
							stage='weekone', send_email_to=TECH,
							action=['noop'], 
							take_action=False, 
							save_act_all=True, 
							date_action_taken=current_time,
							message_index=0, 
							penalty_level=0, )
			record.data.update(rec)

		print "%s" % record.data['log'],
		print "%15s" % record.data['action']
		return record
		
