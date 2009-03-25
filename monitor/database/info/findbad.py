from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all, belongs_to
from elixir import String, Integer as Int, DateTime, PickleType, Boolean
from datetime import datetime,timedelta
import elixir
import traceback
from elixir.ext.versioned import *

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session


#class FindbadNodeRecordSync(Entity):
#	hostname = Field(String(250),primary_key=True) #,alternateMethodName='by_hostname')
#	round    = Field(Int,default=0)
	
#class FindbadPCURecordSync(Entity):
#	plc_pcuid = Field(Int,primary_key=True) #,alternateMethodName='by_pcuid')
#	round     = Field(Int,default=0)

class FindbadNodeRecord(Entity):
	@classmethod
	def get_all_latest(cls):
		return cls.query.all()
		#fbsync = FindbadNodeRecordSync.get_by(hostname="global")
		#if fbsync:
		#	return cls.query.filter_by(round=fbsync.round)
		#else:
		#	return []

	@classmethod
	def get_latest_by(cls, **kwargs):
		return cls.query.filter_by(**kwargs).first()
		#fbsync = FindbadNodeRecordSync.get_by(hostname="global")
		#if fbsync:
		#	kwargs['round'] = fbsync.round
		#	return cls.query.filter_by(**kwargs).order_by(FindbadNodeRecord.date_checked.desc())
		#else:
		#	return []

	@classmethod
	def get_latest_n_by(cls, n=3, **kwargs):
		return cls.query.filter_by(**kwargs)
		#fbsync = FindbadNodeRecordSync.get_by(hostname="global")
		#kwargs['round'] = fbsync.round
		#ret = []
		#for i in range(0,n):
		#	kwargs['round'] = kwargs['round'] - i
		#	f = cls.query.filter_by(**kwargs).first()
		#	if f:
		#		ret.append(f)
		#return ret

# ACCOUNTING
	date_checked = Field(DateTime,default=datetime.now)
	round = Field(Int,default=0)
	hostname = Field(String,primary_key=True,default=None)
	loginbase = Field(String)

# INTERNAL
	kernel_version = Field(String,default=None)
	bootcd_version = Field(String,default=None)
	nm_status = Field(String,default=None)
	fs_status = Field(String,default=None)
	dns_status = Field(String,default=None)
	princeton_comon_dir = Field(Boolean,default=False)
	princeton_comon_running = Field(Boolean,default=False)
	princeton_comon_procs = Field(Int,default=None)

# EXTERNAL
	plc_node_stats = Field(PickleType,default=None)
	plc_site_stats = Field(PickleType,default=None)
	plc_pcuid      = Field(Int,default=None)
	comon_stats    = Field(PickleType,default=None)
	port_status    = Field(PickleType,default=None)
	ssh_portused = Field(Int,default=22)
	ssh_status = Field(Boolean,default=False)
	ssh_error = Field(String,default=None)	# set if ssh_access == False
	ping_status = Field(Boolean,default=False)

# INFERRED
	observed_category = Field(String,default=None)
	observed_status = Field(String,default=None)

	acts_as_versioned(ignore=['date_checked'])
	# NOTE: this is the child relation
	#action = ManyToOne('ActionRecord', required=False)

class FindbadPCURecord(Entity):
	@classmethod
	def get_all_latest(cls):
		return cls.query.all()

	@classmethod
	def get_latest_by(cls, **kwargs):
		return cls.query.filter_by(**kwargs)

# ACCOUNTING
	date_checked = Field(DateTime)
	round = Field(Int,default=0)
	plc_pcuid = Field(Int) #alternateID=True,alternateMethodName='by_pcuid')

# EXTERNAL
	plc_pcu_stats = Field(PickleType,default=None)
	dns_status = Field(String)
	port_status = Field(PickleType)
	entry_complete = Field(String)

# INTERNAL
# INFERRED
	reboot_trial_status = Field(String)

	acts_as_versioned(ignore=['date_checked'])
