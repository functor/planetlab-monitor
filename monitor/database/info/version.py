from elixir import Entity, Field
from elixir import Integer
from elixir import options_defaults, using_options, setup_all

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

from monitor.monitor_version import monitor_version

major_version = int(monitor_version.split('.')[0])
minor_version = int(monitor_version.split('.')[-1])

class DBVersion(Entity):
	major = Field(Integer, required=True, default=major_version)
	minor = Field(Integer, required=True, default=minor_version)

