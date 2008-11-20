#__connection__ = hub = PackageHub('infovacuum')
try:
	import pkg_resources
	pkg_resources.require("SQLAlchemy>=0.4.9")
	pkg_resources.require("Elixir>=0.4.0")
	## NOTE!!!!!!
	# with this line enabled, other models cannot import this file.
	# it results in the wrong metadata value being loaded, I think.
	#from turbogears.database import metadata, mapper

	#import pkg_resources
	#pkg_resources.require("SQLObject>=0.7.1")
	#from turbogears.database import PackageHub, AutoConnectHub
	#from turbogears import config
	#uri = config.get("sqlobject.dburi")
	#from sqlobject import connectionForURI,sqlhub
	#sqlhub.processConnection = connectionForURI(uri)

except:
	# NOTE:  this try, will allow external modules to import the model without
	# requring the turbogears garbage.
	import traceback
	print traceback.print_exc()
	pass

from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all
from elixir import String, Unicode, Integer, DateTime
options_defaults['autosetup'] = False

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session

def findby_or_create(cls, if_new_set={}, **kwargs):
	result = cls.get_by(**kwargs)
	if not result:
		result = cls(**kwargs)
		result.set(**if_new_set)
	return result
Entity.findby_or_create = classmethod(findby_or_create)

from monitor.database.infovacuum.actionrecord import *
from monitor.database.infovacuum.findbad import *
from monitor.database.infovacuum.historyrecord import *
setup_all()
