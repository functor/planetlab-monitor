
from monitor import reboot
from monitor.common import *
from monitor.model import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.wrapper.emailTxt import mailtxt
from monitor.database.info.model import *

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
		
		args = {'loginbase' : self.db.loginbase, 
				'penalty_level' : self.db.penalty_level,
				'monitor_hostname' : config.MONITOR_HOSTNAME,
				'support_email'   : config.support_email,
				'plc_name' : config.PLC_NAME,
				'plc_hostname' : config.PLC_WWW_HOSTNAME}
		args.update(kwargs)

		hostname = None
		if 'hostname' in args:
			hostname = args['hostname']

		if hasattr(mailtxt, type):

			message = getattr(mailtxt, type)

			saveact = True
			viart = True
			if 'viart' in kwargs: 
				saveact = kwargs['viart']
				viart = kwargs['viart']

			if 'saveact' in kwargs: 
				saveact = kwargs['saveact']

			if viart:
				self.getTicketStatus()		# get current message status
				if self.db.message_status not in ['open', 'new']:
					self.closeTicket()

			m = Message(message[0] % args, message[1] % args, viart, self.db.message_id)

			contacts = self.getContacts()
			#contacts = [config.cc_email]

			print "sending message: %s to site %s for host %s" % (type, self.db.loginbase, hostname)

			ret = m.send(contacts)
			if viart:
				self.db.message_id = ret
				# reset to previous status, since a new subject 'opens' RT tickets.
				self.setTicketStatus(self.db.message_status) 

			if saveact:
				# NOTE: only make a record of it if it's in RT.
				act = ActionRecord(loginbase=self.db.loginbase, hostname=hostname, action='notice', 
								action_type=type, message_id=self.db.message_id)

		else:
			print "+-- WARNING! ------------------------------"
			print "| No such message name in emailTxt.mailtxt: %s" % type
			print "+------------------------------------------"

		return

	def closeTicket(self):
		if self.db.message_id:
			mailer.closeTicketViaRT(self.db.message_id, "Ticket Closed by Monitor")
			act = ActionRecord(loginbase=self.db.loginbase, action='notice', 
								action_type='close_ticket', message_id=self.db.message_id)
			self.db.message_id = 0
			self.db.message_status = "new"

	def runBootManager(self, hostname):
		from monitor import bootman
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
		err = ""
		try:
			ret = reboot.reboot_str(hostname)
		except Exception, e:
			err = traceback.format_exc()
			ret = str(e)

		if ret == 0 or ret == "0":
			ret = ""

		act = ActionRecord(loginbase=self.db.loginbase,
							hostname=hostname,
							action='reboot',
							action_type='try_reboot',
							error_string=err)

