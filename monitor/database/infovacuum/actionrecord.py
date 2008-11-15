from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all, has_one
from elixir import String, Integer, DateTime, PickleType, Boolean
from datetime import datetime,timedelta
import elixir
import traceback

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

class IssueType(Entity):
	shortname = Field(String, default=None)
	description = Field(String, default=None)
	issue_record = ManyToMany('IssueRecord')

class IssueRecord(Entity):
	date_created = Field(DateTime,default=datetime.now)
	date_last_updated = Field(DateTime,default=datetime.now)
	date_action_taken = Field(DateTime,default=datetime.now)

	hostname = Field(String,default=None)
	loginbase = Field(String)

	ticket_id = Field(Integer, default=0)
	rt = Field(PickleType, default=None)

	# open, paused, closed
	status = Field(String, default="open")

	take_action = Field(Boolean, default=False)
	send_email = Field(Boolean, default=True)

	message_series =  Field(String, default="nodedown")
	message_index = Field(Integer, default=0)
	penalty_level = Field(Integer, default=0)

	issue_type = ManyToMany('IssueType')
	actions = OneToMany('ActionRecord', order_by='-date_created')


class ActionRecord(Entity):
	@classmethod
	def get_latest_by(cls, **kwargs):
		# TODO: need to sort on 'round' since actions will not be globally sync'd.
		return cls.query.filter_by(**kwargs).order_by(ActionRecord.id.desc()).first()

# ACCOUNTING
	date_created = Field(DateTime,default=datetime.now)
	hostname = Field(String,default=None)
	loginbase = Field(String)

	issue = ManyToOne('IssueRecord')
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
	findbad_records = OneToMany('FindbadNodeRecord', order_by='-date_checked')

	# NOTE: can I move 'message_index, escellation_level, and penalty_level'
	#    into the same value?  Maybe not penalty level, since there are only two;
	#    and, there may be additional message and escellation levels.
	send_email_to = Field(PickleType, default=None)
	action_description = Field(PickleType, default=None)
	message_arguments = Field(PickleType, default=None)

	# NOTE: not sure this needs to be in the db.
	escellation_level = Field(Integer, default=0)
	stage = Field(String, default=None)
