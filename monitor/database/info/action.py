from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all, has_one
from elixir import String, Integer, DateTime, PickleType, Boolean
from elixir.ext.versioned import *
from datetime import datetime,timedelta
import elixir
import traceback

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

#class IssueType(Entity):
#	shortname = Field(String, default=None)
#	description = Field(String, default=None)
#	issue_record = ManyToMany('IssueRecord')

#class IssueRecord(Entity):
#	date_created = Field(DateTime,default=datetime.now)
#	date_last_updated = Field(DateTime,default=datetime.now)
#	date_action_taken = Field(DateTime,default=datetime.now)
#
#	hostname = Field(String,default=None)
#	loginbase = Field(String)
#
#	ticket_id = Field(Integer, default=0)
#	rt = Field(PickleType, default=None)
#
#	# open, paused, closed
#	status = Field(String, default="open")
#
#	take_action = Field(Boolean, default=False)
#	send_email = Field(Boolean, default=True)
#
#	message_series =  Field(String, default="nodedown")
#	message_index = Field(Integer, default=0)
#	penalty_level = Field(Integer, default=0)
#
#	issue_type = ManyToMany('IssueType')
#	actions = OneToMany('ActionRecord', order_by='-date_created')

class BlacklistRecord(Entity):
	date_created = Field(DateTime,default=datetime.now)
	hostname = Field(String,default=None)
	loginbase = Field(String,default=None)
	expires = Field(Integer,default=0)	# seconds plus 
	acts_as_versioned(['hostname'])

	@classmethod
	def getLoginbaseBlacklist(cls):
		# TODO: need to sort on 'round' since actions will not be globally sync'd.
		return cls.query.filter(cls.loginbase!=None).order_by(cls.loginbase.desc())

	@classmethod
	def getHostnameBlacklist(cls):
		# TODO: need to sort on 'round' since actions will not be globally sync'd.
		return cls.query.filter(cls.hostname!=None).order_by(cls.hostname.desc())

	def neverExpires(self):
		if self.expires == 0:
			return True
		else:
			return False

	def expired(self):
		if self.neverExpires():
			return False
		else:
			if self.date_created + timedelta(0,self.expires) > datetime.now():
				return False
			else:
				return True

	def willExpire(self):
		if self.neverExpires():
			return "never"
		else:
			return self.date_created + timedelta(0, self.expires)

class BootmanSequenceRecord(Entity):
	sequence = Field(String, primary_key=True, default=None)
	action   = Field(String, default=None)
	date_created = Field(DateTime,default=datetime.now)

class ActionRecord(Entity):
	@classmethod
	def get_latest_by(cls, **kwargs):
		# TODO: need to sort on 'round' since actions will not be globally sync'd.
		return cls.query.filter_by(**kwargs).order_by(ActionRecord.id.desc()).first()

	@classmethod
	def delete_recent_by(cls, since, **kwargs):
		acts = cls.query.filter_by(**kwargs).filter(cls.date_created >= datetime.now() - timedelta(since)).order_by(cls.date_created.desc())
		for i in acts: i.delete()

	# ACCOUNTING
	date_created = Field(DateTime,default=datetime.now)
	loginbase = Field(String,default=None)
	hostname = Field(String,default=None)
	# NOTE:
	#	the expected kinds of actions are:
	#		* reboot node
	#		* open ticket, send notice 
	#		* close ticket
	#		* apply penalty to site
	#		* backoff penalty to site
	action = Field(String)

	# NOTE: describes the kind of action.  i.e. online-notice, offline-notice,
	# reboot-first-try, reboot-second-try, penalty-pause, penalty-warning, penalty-no-create,
	# penalty-disable-slices, 
	action_type = Field(String, default=None)

	message_id = Field(Integer, default=0)
	penalty_level = Field(Integer, default=0)

	# NOTE: in case an exception is thrown while trying to perform an action.
	error_string = Field(String, default=None)

	log_path = Field(String, default=None)

	#issue = ManyToOne('IssueRecord')
	# NOTE: this is the parent relation to fb records.  first create the
	# action record, then append to this value all of the findbad records we
	# want to have in our set.
	# Model:
	#    - create action record
	#    - find fbnode records
	#    - append fbnode records to action record
	#  OR
	#    - find fbnode records
	#    - create action record with fbnodes as argument
	# findbad_records = OneToMany('FindbadNodeRecord', order_by='-date_checked')

	# NOTE: can I move 'message_index, escellation_level, and penalty_level'
	#    into the same value?  Maybe not penalty level, since there are only two;
	#    and, there may be additional message and escellation levels.
	#send_email_to = Field(PickleType, default=None)
	#action_description = Field(PickleType, default=None)
	#message_arguments = Field(PickleType, default=None)

	# NOTE: not sure this needs to be in the db.
	#escellation_level = Field(Integer, default=0)
	#stage = Field(String, default=None)
