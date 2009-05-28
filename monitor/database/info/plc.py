from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all
from elixir import PickleType, String, Integer, DateTime, Boolean
from elixir.ext.versioned import *

from datetime import datetime,timedelta

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

class PlcSite(Entity):
	site_id = Field(Integer,primary_key=True)
	loginbase = Field(String,default=None)
	date_checked = Field(DateTime,default=datetime.now)

	plc_site_stats = Field(PickleType,default=None)
	acts_as_versioned(ignore=['date_checked'])

class PlcNode(Entity):
	node_id = Field(Integer,primary_key=True)
	hostname = Field(String,default=None)
	date_checked = Field(DateTime,default=datetime.now)

	plc_node_stats = Field(PickleType,default=None)
	acts_as_versioned(ignore=['date_checked'])

class PlcPCU(Entity):
	pcu_id = Field(Integer,primary_key=True)
	date_checked = Field(DateTime,default=datetime.now)

	plc_pcu_stats = Field(PickleType,default=None)
	acts_as_versioned(ignore=['date_checked'])

class PlcPCU2(Entity):
	pcu_id = Field(Integer,primary_key=True)
	date_checked = Field(DateTime,default=datetime.now)

	site_id = Field(Integer, default=0)
	protocol = Field(String, default=None)
	node_ids = Field(PickleType,default=None)
	ports = Field(PickleType,default=None)
	hostname = Field(String, default=None)
	ip = Field(String, default=None)
	username = Field(String, default=None)
	password = Field(String, default=None)
	model = Field(String, default=None)
	notes = Field(String, default=None)

	acts_as_versioned(ignore=['date_checked'])
