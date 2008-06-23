#!/usr/bin/python

import soltesz

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import config
import mailer
import time

def gethostlist(hostlist_file):
	return config.getListFromFile(hostlist_file)
	
	#nodes = api.GetNodes({'peer_id' : None}, ['hostname'])
	#return [ n['hostname'] for n in nodes ]

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

def cmpValMap(v1, v2, map):
	if v1 in map and v2 in map and map[v1] < map[v2]:
		return 1
	elif v1 in map and v2 in map and map[v1] > map[v2]:
		return -1
	elif v1 in map and v2 in map:
		return 0
	else:
		raise Exception("No index %s or %s in map" % (v1, v2))

def cmpCategoryVal(v1, v2):
	map = array_to_priority_map([ None, 'ALPHA', 'PROD', 'OLDBOOTCD', 'UNKNOWN', 'FORCED', 'ERROR', ])
	return cmpValMap(v1,v2,map)


class PCU:
	def __init__(self, hostname):
		self.hostname = hostname

	def reboot(self):
		return True
	def available(self):
		return True
	def previous_attempt(self):
		return True
	def setValidMapping(self):
		pass

class Penalty:
	def __init__(self, key, valuepattern, action):
		pass

class PenaltyMap:
	def __init__(self):
		pass

	# connect one penalty to another, in a FSM diagram.  After one
	# 	condition/penalty is applied, move to the next phase.


fb = soltesz.dbLoad("findbad")

class RT(object):
	def __init__(self, ticket_id = None):
		self.ticket_id = ticket_id
		if self.ticket_id:
			print "getting ticket status",
			self.status = mailer.getTicketStatus(self.ticket_id)
			print self.status

	def setTicketStatus(self, status):
		mailer.setTicketStatus(self.ticket_id, status)
		self.status = mailer.getTicketStatus(self.ticket_id)
		return True
	
	def getTicketStatus(self):
		if not self.status:
			self.status = mailer.getTicketStatus(self.ticket_id)
		return self.status

	def closeTicket(self):
		mailer.closeTicketViaRT(self.ticket_id) 

	def email(self, subject, body, to):
		self.ticket_id = mailer.emailViaRT(subject, body, to, self.ticket_id)
		return self.ticket_id

class Message(object):
	def __init__(self, subject, message, via_rt=True, ticket_id=None, **kwargs):
		self.via_rt = via_rt
		self.subject = subject
		self.message = message
		self.rt = RT(ticket_id)

	def send(self, to):
		if self.via_rt:
			return self.rt.email(self.subject, self.message, to)
		else:
			return mailer.email(self.subject, self.message, to)

class Recent(object):
	def __init__(self, withintime):
		self.withintime = withintime
		self.time = time.time()
		self.action_taken = False

	def isRecent(self):
		if self.time + self.withintime < time.time():
			self.action_taken = False

		if self.time + self.withintime > time.time() and self.action_taken:
			return True
		else:
			return False

	def unsetRecent(self):
		self.action_taken = False
		self.time = time.time()
		return True

	def setRecent(self):
		self.action_taken = True
		self.time = time.time()
		return True
		
class PersistFlags(Recent):
	def __new__(typ, id, *args, **kwargs):
		if 'db' in kwargs:
			db = kwargs['db']
			del kwargs['db']
		else:
			db = "persistflags"

		try:
			pm = soltesz.dbLoad(db)
		except:
			soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)
		#print pm
		if id in pm:
			obj = pm[id]
		else:
			obj = super(PersistFlags, typ).__new__(typ, *args, **kwargs)
			for key in kwargs.keys():
				obj.__setattr__(key, kwargs[key])

		obj.db = db
		return obj

	def __init__(self, id, withintime, **kwargs):
		self.id = id
		Recent.__init__(self, withintime)

	def save(self):
		pm = soltesz.dbLoad(self.db)
		pm[self.id] = self
		soltesz.dbDump(self.db, pm)

	def resetFlag(self, name):
		self.__setattr__(name, False)

	def setFlag(self, name):
		self.__setattr__(name, True)
		
	def getFlag(self, name):
		try:
			return self.__getattribute__(name)
		except:
			self.__setattr__(name, False)
			return False

	def setRecentFlag(self, name):
		self.setFlag(name)
		self.setRecent()

	def getRecentFlag(self, name):
		# if recent and flag set -> true
		# else false
		try:
			return self.isRecent() & self.__getattribute__(name)
		except:
			self.__setattr__(name, False)
			return False

class PersistMessage(Message):
	def __new__(typ, id, subject, message, via_rt, **kwargs):
		if 'db' in kwargs:
			db = kwargs['db']
		else:
			db = "persistmessages"

		try:
			pm = soltesz.dbLoad(db)
		except:
			soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)

		#print pm
		if id in pm:
			print "Using existing object"
			obj = pm[id]
		else:
			print "creating new object"
			obj = super(PersistMessage, typ).__new__(typ, [id, subject, message, via_rt], **kwargs)
			obj.id = id
			obj.actiontracker = Recent(3*60*60*24)
			obj.ticket_id = None

		obj.db = db
		return obj

	def __init__(self, id, subject, message, via_rt=True, **kwargs):
		print "initializing object: %s" % self.ticket_id
		self.id = id
		Message.__init__(self, subject, message, via_rt, self.ticket_id)

	def reset(self):
		self.actiontracker.unsetRecent()

	def send(self, to):
		if not self.actiontracker.isRecent():
			self.ticket_id = Message.send(self, to)
			self.actiontracker.setRecent()

			#print "recording object for persistance"
			pm = soltesz.dbLoad(self.db)
			pm[self.id] = self
			soltesz.dbDump(self.db, pm)
		else:
			# NOTE: only send a new message every week, regardless.
			print "Not sending to host b/c not within window of 6 days"
			pass

class MonitorMessage(object):
	def __new__(typ, id, *args, **kwargs):
		if 'db' in kwargs:
			db = kwargs['db']
		else:
			db = "monitormessages"

		try:
			if 'reset' in kwargs and kwargs['reset'] == True:
				soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)
		except:
			soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)

		#print pm
		if id in pm:
			print "Using existing object"
			obj = pm[id]
		else:
			print "creating new object"
			obj = super(object, typ).__new__(typ, id, *args, **kwargs)
			obj.id = id
			obj.sp = PersistSitePenalty(id, 0)

		obj.db = db
		return obj

	def __init__(self, id, message):
		pass
		

class SitePenalty(object):
	penalty_map = [] 
	penalty_map.append( { 'name': 'noop',      		'enable'   : lambda host: None,
													'disable'  : lambda host: None } )
	penalty_map.append( { 'name': 'nocreate',		'enable'   : lambda host: plc.removeSliceCreation(host),
													'disable'  : lambda host: plc.enableSliceCreation(host) } )
	penalty_map.append( { 'name': 'suspendslices',	'enable'   : lambda host: plc.suspendSlices(host),
													'disable'  : lambda host: plc.enableSlices(host) } )

	#def __init__(self, index=0, **kwargs):
	#	self.index = index

	def get_penalties(self):
		# TODO: get penalties actually applied to a node from PLC DB.
		return [ n['name'] for n in SitePenalty.penalty_map ] 

	def increase(self):
		self.index = self.index + 1
		if self.index > len(SitePenalty.penalty_map)-1: self.index = len(SitePenalty.penalty_map)-1
		return True

	def decrease(self):
		self.index = self.index - 1
		if self.index < 0: self.index = 0
		return True

	def apply(self, host):

		for i in range(len(SitePenalty.penalty_map)-1,self.index,-1):
			print "\tdisabling %s on %s" % (SitePenalty.penalty_map[i]['name'], host)
			SitePenalty.penalty_map[i]['disable'](host)

		for i in range(0,self.index+1):
			print "\tapplying %s on %s" % (SitePenalty.penalty_map[i]['name'], host)
			SitePenalty.penalty_map[i]['enable'](host)

		return



class PersistSitePenalty(SitePenalty):
	def __new__(typ, id, index, **kwargs):
		if 'db' in kwargs:
			db = kwargs['db']
		else:
			db = "persistpenalties"

		try:
			if 'reset' in kwargs and kwargs['reset'] == True:
				soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)
		except:
			soltesz.dbDump(db, {})
			pm = soltesz.dbLoad(db)

		#print pm
		if id in pm:
			print "Using existing object"
			obj = pm[id]
		else:
			print "creating new object"
			obj = super(PersistSitePenalty, typ).__new__(typ, [index], **kwargs)
			obj.id = id
			obj.index = index

		obj.db = db
		return obj

	def __init__(self, id, index, **kwargs):
		self.id = id
		#SitePenalty.__init__(self, self.index)

	def save(self):
		pm = soltesz.dbLoad(self.db)
		pm[self.id] = self
		soltesz.dbDump(self.db, pm)



class Target:
	"""
		Each host has a target set of attributes.  Some may be set manually,
		or others are set globally for the preferred target.

		For instance:
			All nodes in the Alpha or Beta group would have constraints like:
				[ { 'state' : 'BOOT', 'kernel' : '2.6.22' } ]
	"""
	def __init__(self, constraints):
		self.constraints = constraints

	def verify(self, data):
		"""
			self.constraints is a list of key, value pairs.
			# [ {... : ...}==AND , ... , ... , ] == OR
		"""
		con_or_true = False
		for con in self.constraints:
			#print "con: %s" % con
			con_and_true = True
			for key in con.keys():
				#print "looking at key: %s" % key
				if key in data: 
					#print "%s %s" % (con[key], data[key])
					con_and_true = con_and_true & (con[key] in data[key])
				elif key not in data:
					print "missing key %s" % key
					con_and_true = False

			con_or_true = con_or_true | con_and_true

		return con_or_true

class NodeRecord:
	def __init__(self, hostname, target):
		self.hostname = hostname
		self.pcu = PCU(hostname)
		self.ticket = None
		self.target = target
		if hostname in fb['nodes']:
			self.data = fb['nodes'][hostname]['values']
		else:
			raise Exception("Hostname not in scan database")

	def get(self):
		pass
	def severity(self):
		category = self.data['category']
		prev_category = self.data['prev_category']
		val = cmpCategoryVal(category, prev_category)
		return val 
	def open_tickets(self):
		if self.ticket and self.ticket.status['status'] == 'open':
			return 1
		return 0
	def setIntrospect(self):
		pass

	def email_notice(self):
		message = self._get_message_for_condition()
		message.send(self._get_contacts_for_condition())
		return True
	def close_ticket(self):
		if self.ticket:
			self.ticket.closeTicket()

	def exempt_from_penalties(self):
		bl = soltesz.dbLoad("l_blacklist")
		return self.hostname in bl

	def penalties(self):
		return []
	def escellate_penalty(self):
		return True
	def reduce_penalty(self):
		return True


	def atTarget(self):
		return self.target.verify(self.data)

	def _get_condition(self):
		return self.data['category'].lower()

	def _get_stage(self):
		"improvement"
		"firstnotice_noop"
		"secondnotice_noslicecreation"
		"thirdnotice_disableslices"

		delta = current_time - self.data['time']

	def _get_message_for_condition(self):
		pass
	def _get_contacts_for_condition(self):
		pass

if __name__ == "__main__":
	#r = RT()
	#r.email("test", "body of test message", ['soltesz@cs.princeton.edu'])
	from emailTxt import mailtxt
	soltesz.dbDump("persistmessages", {});
	args = {'url_list': 'http://www.planet-lab.org/bootcds/planet1.usb\n','hostname': 'planet1','hostname_list': ' blahblah -  days down\n'}
	m = PersistMessage("blue", "test 1", mailtxt.newdown_one[1] % args, True)
	m.send(['soltesz@cs.utk.edu'])
	m = PersistMessage("blue", "test 1 - part 2", mailtxt.newalphacd_one[1] % args, True)
	# TRICK timer to thinking some time has passed.
	m.actiontracker.time = time.time() - 6*60*60*24
	m.send(['soltesz@cs.utk.edu'])
