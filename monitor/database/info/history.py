from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all
from elixir import String, Integer as Int, DateTime, Boolean
from datetime import datetime,timedelta

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

# your data model
class HistoryNodeRecord(Entity):
	hostname = Field(String(250),primary_key=True)
	last_checked = Field(DateTime,default=datetime.now)
	last_changed = Field(DateTime,default=datetime.now)
	status = Field(String,default="unknown")

	@classmethod
	def by_hostname(cls, hostname):
		return cls.query.filter_by(hostname=hostname).first()

class HistoryPCURecord(Entity):
	plc_pcuid = Field(Int,primary_key=True)

	last_checked = Field(DateTime,default=datetime.now)
	last_changed = Field(DateTime,default=datetime.now)
	status = Field(String,default="unknown")

	last_valid = Field(DateTime,default=None)
	valid  = Field(String,default="unknown")

	@classmethod
	def by_pcuid(cls, pcuid):
		return cls.query.filter_by(pcuid=pcuid).first()

class HistorySiteRecord(Entity):
	loginbase = Field(String(250),primary_key=True)

	last_checked = Field(DateTime,default=datetime.now)
	last_changed = Field(DateTime,default=datetime.now)

	nodes_total = Field(Int,default=0)
	nodes_up = Field(Int,default=0)
	slices_total = Field(Int,default=0)
	slices_used = Field(Int,default=0)

	# all nodes offline and never-contact.
	new = Field(Boolean,default=False)

	enabled = Field(Boolean,default=False)

	status = Field(String,default="unknown")

	message_id = Field(Int, default=0)
	message_status = Field(String, default=None)
	message_queue = Field(String, default=None) 
	message_created = Field(DateTime, default=None)

	penalty_level   = Field(Int, default=0)
	penalty_applied = Field(Boolean, default=False)

	@classmethod
	def by_loginbase(cls, loginbase):
		return cls.query.filter_by(loginbase=loginbase).first()
	
