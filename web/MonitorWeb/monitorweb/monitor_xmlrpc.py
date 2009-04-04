import sys
import xmlrpclib
import cherrypy
import turbogears
from datetime import datetime, timedelta
import time

from monitor.database.info.model import *
from monitor.database.info.interface import *

class MonitorXmlrpcServerMethods:
	@cherrypy.expose
	def listMethods(self):
		mod = MonitorXmlrpcServer()
		ret_list = []
		for f in dir(mod):
			if isinstance(mod.__getattribute__(f),type(mod.__getattribute__('addDowntime'))):
				ret_list += [f]
		return ret_list

def convert_datetime(d, keys=None):
	ret = d.copy()
	n = datetime.now()
	if keys == None:
		keys = d.keys()
	for k in keys:
		if type(d[k]) == type(n):
			ret[k] = time.mktime(d[k].utctimetuple())
	
	return ret

class MonitorXmlrpcServer(object):

	@cherrypy.expose
	def listMethods(self):
		mod = MonitorXmlrpcServer()
		ret_list = []
		for f in dir(mod):
			if isinstance(mod.__getattribute__(f),type(mod.__getattribute__('addDowntime'))):
				ret_list += [f]
		return ret_list

	@turbogears.expose()
	def XMLRPC(self):
		params, method = xmlrpclib.loads(cherrypy.request.body.read())
		try:
			if method == "xmlrpc":
				# prevent recursion
				raise AssertionError("method cannot be 'xmlrpc'")
			# Get the function and make sure it's exposed.
			method = getattr(self, method, None)
			# Use the same error message to hide private method names
			if method is None or not getattr(method, "exposed", False):
				raise AssertionError("method does not exist")

			session.clear()
			# Call the method, convert it into a 1-element tuple
			# as expected by dumps					   
			response = method(*params)

			session.flush()
			response = xmlrpclib.dumps((response,), methodresponse=1, allow_none=1)
		except xmlrpclib.Fault, fault:
			# Can't marshal the result
			response = xmlrpclib.dumps(fault, allow_none=1)
		except:
			# Some other error; send back some error info
			response = xmlrpclib.dumps(
				xmlrpclib.Fault(1, "%s:%s" % (sys.exc_type, sys.exc_value))
				)

		cherrypy.response.headers["Content-Type"] = "text/xml"
		return response

	# User-defined functions must use cherrypy.expose; turbogears.expose
	# 	does additional checking of the response type that we don't want.
	@cherrypy.expose
	def upAndRunning(self):
		return True

	# SITES ------------------------------------------------------------

	@cherrypy.expose
	def getSiteStatus(self, auth):
		ret_list = []
		sites = HistorySiteRecord.query.all()
		for q in sites:
			d = q.to_dict(exclude=['timestamp', 'version', ])
			d = convert_datetime(d, ['last_checked', 'last_changed', 'message_created'])
			ret_list.append(d)
		return ret_list

	@cherrypy.expose
	def clearSitePenalty(self, auth, loginbase):
		sitehist = SiteInterface.get_or_make(loginbase=loginbase)
		sitehist.clearPenalty()
		#sitehist.applyPenalty()
		#sitehist.sendMessage('clear_penalty')
		sitehist.closeTicket()
		return True

	@cherrypy.expose
	def increaseSitePenalty(self, auth, loginbase):
		sitehist = SiteInterface.get_or_make(loginbase=loginbase)
		sitehist.increasePenalty()
		#sitehist.applyPenalty()
		#sitehist.sendMessage('increase_penalty')
		return True

	# NODES ------------------------------------------------------------

	@cherrypy.expose
	def getNodeStatus(self, auth):
		ret_list = []
		sites = HistoryNodeRecord.query.all()
		for q in sites:
			d = q.to_dict(exclude=['timestamp', 'version', ])
			d = convert_datetime(d, ['last_checked', 'last_changed',])
			ret_list.append(d)
		return ret_list

	@cherrypy.expose
	def getRecentActions(self, auth, loginbase=None, hostname=None):
		ret_list = []
		return ret_list

	# BLACKLIST ------------------------------------------------------------

	@cherrypy.expose
	def getBlacklist(self, auth):
		bl = BlacklistRecord.query.all()
		ret_list = []
		for q in bl:
			d = q.to_dict(exclude=['timestamp', 'version', 'id', ])
			d = convert_datetime(d, ['date_created'])
			ret_list.append(d)

		return ret_list
		# datetime.datetime.fromtimestamp(time.mktime(time.strptime(mytime, time_format)))
	
	@cherrypy.expose
	def addHostToBlacklist(self, auth, hostname, expires=0):
		bl = BlacklistRecord.findby_or_create(hostname=hostname, expires=expires)
		return True

	@cherrypy.expose
	def addSiteToBlacklist(self, auth, loginbase, expires=0):
		bl = BlacklistRecord.findby_or_create(hostname=hostname, expires=expires)
		return True

	@cherrypy.expose
	def deleteFromBlacklist(self, auth, loginbase=None, hostname=None):
		if (loginbase==None and hostname == None) or (loginbase != None and hostname != None):
			raise Exception("Please specify a single record to delete: either hostname or loginbase")
		elif loginbase != None:
			bl = BlacklistRecord.get_by(loginbase=loginbase)
			bl.delete()
		elif hostname != None:
			bl = BlacklistRecord.get_by(hostname=hostname)
			bl.delete()
		return True
