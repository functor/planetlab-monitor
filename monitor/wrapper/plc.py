#
# plc.py
#
# Helper functions that minipulate the PLC api.
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu
#
# $Id: plc.py,v 1.18 2007/08/29 17:26:50 soltesz Exp $
#

import xml, xmlrpclib
import logging
import time
import traceback
from datetime import datetime

# note: this needs to be consistent with the value in PLEWWW/planetlab/includes/plc_functions.php
PENDING_CONSORTIUM_ID = 0
# not used in monitor
#APPROVED_CONSORTIUM_ID = 999999

try:
	from monitor import config
	debug = config.debug
	XMLRPC_SERVER=config.API_SERVER
except:
	debug = False
	# NOTE: this host is used by default when there are no auth files.
	XMLRPC_SERVER="https://boot.planet-lab.org/PLCAPI/"

global_log_api = True
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s : %(message)s',
                    datefmt='%s %Y-%m-%dT%H:%M:%S',
                    filename='/usr/share/monitor/myops-api-log.log',
                    filemode='a')
apilog = logging.getLogger("api")

def log_api_call(name, *params):
    logstr = "%s(" %name
    for x in params:
        logstr += "%s," % x
    logstr = logstr[:-1] + ")"
    if global_log_api: apilog.debug(logstr)

logger = logging.getLogger("monitor")
	
class Auth:
	def __init__(self, username=None, password=None, **kwargs):
		if 'session' in kwargs:
			self.auth= { 'AuthMethod' : 'session',
					'session' : kwargs['session'] }
		else:
			if username==None and password==None:
				self.auth = {'AuthMethod': "anonymous"}
			else:
				self.auth = {'Username' : username,
							'AuthMethod' : 'password',
							'AuthString' : password}


# NOTE: by default, use anonymous access, but if auth files are 
#       configured, use them, with their auth definitions.
auth = Auth()
try:
	from monitor import config
	auth.auth = {'Username' : config.API_AUTH_USER,
	             'AuthMethod' : 'password',
				 'AuthString' : config.API_AUTH_PASSWORD}
	auth.server = config.API_SERVER
except:
	try:
		import auth
		auth.server = auth.plc
	except:
		auth = Auth()
		auth.server = XMLRPC_SERVER

global_error_count = 0

class PLC:
	def __init__(self, auth, url):
		self.auth = auth
		self.url = url
		self.api = xmlrpclib.Server(self.url, verbose=False, allow_none=True)

	def __getattr__(self, name):
		method = getattr(self.api, name)
		if method is None:
			raise AssertionError("method does not exist")

		try:
			def call_method(aut, *params):
				if global_log_api: log_api_call(name, *params)
				return method(aut, *params)
			return lambda *params : call_method(self.auth, *params)
			#return lambda *params : method(self.auth, *params)
		except xmlrpclib.ProtocolError:
			traceback.print_exc()
			global_error_count += 1
			if global_error_count >= 10:
				print "maximum error count exceeded; exiting..."
				sys.exit(1)
			else:
				print "%s errors have occurred" % global_error_count
			raise Exception("ProtocolError continuing")

	def __repr__(self):
		return self.api.__repr__()


api = PLC(auth.auth, auth.server)


def getAPI(url):
	return xmlrpclib.Server(url, verbose=False, allow_none=True)

def getNodeAPI(session):
	nodeauth = Auth(session=session)
	return PLC(nodeauth.auth, auth.server)

def getAuthAPI(url=None):
	if url:
		return PLC(auth.auth, url)
	else:
		return PLC(auth.auth, auth.server)

def getCachedAuthAPI():
	return CachedPLC(auth.auth, auth.server)

def getSessionAPI(session, server):
	nodeauth = Auth(session=session)
	return PLC(nodeauth.auth, server)
def getUserAPI(username, password, server):
	auth = Auth(username,password)
	return PLC(auth.auth, server)

def getTechEmails(loginbase):
	"""
		For the given site, return all user email addresses that have the 'tech' role.
	"""
	api = getAuthAPI()
	# get site details.
	s = api.GetSites(loginbase)[0]
	# get people at site
	p = api.GetPersons(s['person_ids'])
	# pull out those with the right role.
	emails = []
	for person in filter(lambda x: 'tech' in x['roles'], p):
		if not isPersonExempt(person['email']):
			emails.append(person['email'])
	#emails = [ person['email'] for person in filter(lambda x: 'tech' in x['roles'], p) ]
	return emails

def getPIEmails(loginbase):
	"""
		For the given site, return all user email addresses that have the 'tech' role.
	"""
	api = getAuthAPI()
	# get site details.
	s = api.GetSites(loginbase)[0]
	# get people at site
	p = api.GetPersons(s['person_ids'])
	# pull out those with the right role.
	#emails = [ person['email'] for person in filter(lambda x: 'pi' in x['roles'], p) ]
	emails = []
	for person in filter(lambda x: 'pi' in x['roles'], p):
		if not isPersonExempt(person['email']):
			emails.append(person['email'])
	return emails

def getSliceUserEmails(loginbase):
	"""
		For the given site, return all user email addresses that have the 'tech' role.
	"""
	api = getAuthAPI()
	# get site details.
	s = api.GetSites(loginbase)[0]
	# get people at site
	slices = api.GetSlices(s['slice_ids'])
	people = []
	for slice in slices:
		people += api.GetPersons(slice['person_ids'])
	# pull out those with the right role.
	#emails = [ person['email'] for person in filter(lambda x: 'pi' in x['roles'], people) ]

	emails = []
	for person in people:
		if not isPersonExempt(person['email']):
			emails.append(person['email'])

	unique_emails = [ x for x in set(emails) ]
	return unique_emails

'''
Returns list of nodes in dbg as reported by PLC
'''
def nodesDbg():
	dbgNodes = []
	api = xmlrpclib.Server(auth.server, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	for node in api.GetNodes(anon, {"boot_state":"dbg"},["hostname"]):
		dbgNodes.append(node['hostname'])
	logger.info("%s nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes


'''
Returns loginbase for given nodename
'''
def siteId(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	site_id = api.GetNodes (auth.auth, {"hostname": nodename}, ['site_id'])
	if len(site_id) == 1:
		loginbase = api.GetSites (auth.auth, site_id[0], ["login_base"])
		return loginbase[0]['login_base']
	else:
		print "Not nodes returned!!!!"

'''
Returns list of slices for a site.
'''
def slices(loginbase):
	siteslices = []
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	sliceids = api.GetSites (auth.auth, {"login_base" : loginbase}, ["slice_ids"])[0]['slice_ids']
	for slice in api.GetSlices(auth.auth, {"slice_id" : sliceids}, ["name"]):
		siteslices.append(slice['name'])
	return siteslices

'''
Returns dict of PCU info of a given node.
'''
def getpcu(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	anon = {'AuthMethod': "anonymous"}
        try:
                nodeinfo = api.GetNodes(auth.auth, {"hostname": nodename}, ["pcu_ids", "ports"])[0]
        except IndexError:
                logger.info("Can not find node: %s" % nodename)
                return False
	if nodeinfo['pcu_ids']:
		print nodeinfo
		sitepcu = api.GetPCUs(auth.auth, nodeinfo['pcu_ids'])[0]
		print sitepcu
		print nodeinfo["ports"]
		sitepcu[nodename] = nodeinfo["ports"][0]
		return sitepcu
	else:
		logger.info("%s doesn't have PCU" % nodename)
		return False

def GetPCUs(filter=None, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	pcu_list = api.GetPCUs(auth.auth, filter, fields)
	return pcu_list 

'''
Returns all site nodes for site id (loginbase).
'''
def getSiteNodes(loginbase, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False)
	nodelist = []
	anon = {'AuthMethod': "anonymous"}
	try:
		nodeids = api.GetSites(anon, {"login_base": loginbase}, fields)[0]['node_ids']
		for node in api.GetNodes(anon, {"node_id": nodeids}, ['hostname']):
			nodelist.append(node['hostname'])
	except Exception, exc:
		logger.info("getSiteNodes:  %s" % exc)
		print "getSiteNodes:  %s" % exc
	return nodelist


def getPersons(filter=None, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	persons = []
	try:
		persons = api.GetPersons(auth.auth, filter, fields)
	except Exception, exc:
		print "getPersons:  %s" % exc
		logger.info("getPersons:  %s" % exc)
	return persons

def getSites(filter=None, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	sites = []
	anon = {'AuthMethod': "anonymous"}
	try:
		#sites = api.GetSites(anon, filter, fields)
		sites = api.GetSites(auth.auth, filter, fields)
	except Exception, exc:
		traceback.print_exc()
		print "getSites:  %s" % exc
		logger.info("getSites:  %s" % exc)
	return sites

def getSiteNodes2(loginbase):
	api = xmlrpclib.Server(auth.server, verbose=False)
	nodelist = []
	anon = {'AuthMethod': "anonymous"}
	try:
		nodeids = api.GetSites(anon, {"login_base": loginbase})[0]['node_ids']
		nodelist += getNodes({'node_id':nodeids})
	except Exception, exc:
		logger.info("getSiteNodes2:  %s" % exc)
	return nodelist

def getNodeNetworks(filter=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	nodenetworks = api.GetInterfaces(auth.auth, filter, None)
	return nodenetworks

def getNodes(filter=None, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	nodes = api.GetNodes(auth.auth, filter, fields) 
			#['boot_state', 'hostname', 
			#'site_id', 'date_created', 'node_id', 'version', 'interface_ids',
			#'last_updated', 'peer_node_id', 'ssh_rsa_key' ])
	return nodes


# Check if the site is a pending site that needs to be approved.
def isPendingSite(loginbase):
        api = xmlrpclib.Server(auth.server, verbose=False)
        try:
                site = api.GetSites(auth.auth, loginbase)[0]
        except Exception, exc:
                logger.info("ERROR: No site %s" % loginbase)
                return False

        if not site['enabled'] and site['ext_consortium_id'] == PENDING_CONSORTIUM_ID:
                return True

        return False


'''
Sets boot state of a node.
'''
def nodeBootState(nodename, state):
	api = xmlrpclib.Server(auth.server, verbose=False)
	try:
		return api.UpdateNode(auth.auth, nodename, {'boot_state': state})
	except Exception, exc:
		logger.info("nodeBootState:  %s" % exc)

def updateNodeKey(nodename, key):
	api = xmlrpclib.Server(auth.server, verbose=False)
	try:
		return api.UpdateNode(auth.auth, nodename, {'key': key})
	except Exception, exc:
		logger.info("updateNodeKey:  %s" % exc)

'''
Sends Ping Of Death to node.
'''
def nodePOD(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False)
	logger.info("Sending POD to %s" % nodename)
	try:
		if not debug:
			return api.RebootNode(auth.auth, nodename)
	except Exception, exc:
			logger.info("nodePOD:  %s" % exc)

'''
Freeze all site slices.
'''
def suspendSiteSlices(loginbase):
        if isPendingSite(loginbase):
                msg = "INFO: suspendSiteSlices: Pending Site (%s)" % loginbase
                print msg
                logger.info(msg)
                return

	api = xmlrpclib.Server(auth.server, verbose=False)
	for slice in slices(loginbase):
		logger.info("Suspending slice %s" % slice)
		try:
			if not debug:
			    if not isSliceExempt(slice):
				    api.AddSliceTag(auth.auth, slice, "enabled", "0")
		except Exception, exc:
			logger.info("suspendSlices:  %s" % exc)

'''
Freeze all site slices.
'''
def suspendSlices(nodename):
        loginbase = siteId(nodename)
        suspendSiteSlices(loginbase)


def enableSiteSlices(loginbase):
	if isPendingSite(loginbase):
		msg = "INFO: enableSiteSlices: Pending Site (%s)" % loginbase
		print msg
		logger.info(msg)
		return

	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	for slice in slices(loginbase):
		logger.info("Enabling slices %s" % slice)
		try:
			if not debug:
				slice_list = api.GetSlices(auth.auth, {'name': slice}, None)
				if len(slice_list) == 0:
					return
				slice_id = slice_list[0]['slice_id']
				l_attr = api.GetSliceTags(auth.auth, {'slice_id': slice_id}, None)
				for attr in l_attr:
					if "enabled" == attr['tagname'] and attr['value'] == "0":
						logger.info("Deleted enable=0 attribute from slice %s" % slice)
						api.DeleteSliceTag(auth.auth, attr['slice_tag_id'])
		except Exception, exc:
			logger.info("enableSiteSlices: %s" % exc)
			print "exception: %s" % exc

def enableSlices(nodename):
        loginbase = siteId(nodename)
        enableSiteSlices(loginbase)


#I'm commenting this because this really should be a manual process.  
#'''
#Enable suspended site slices.
#'''
#def enableSlices(nodename, slicelist):
#	api = xmlrpclib.Server(auth.server, verbose=False)
#	for slice in  slices(siteId(nodename)):
#		logger.info("Suspending slice %s" % slice)
#		api.SliceTagAdd(auth.auth, slice, "plc_slice_state", {"state" : "suspended"})
#
def enableSiteSliceCreation(loginbase):
	if isPendingSite(loginbase):
		msg = "INFO: enableSiteSliceCreation: Pending Site (%s)" % loginbase
		print msg
		logger.info(msg)
		return

	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	try:
		logger.info("Enabling slice creation for site %s" % loginbase)
		if not debug:
			site = api.GetSites(auth.auth, loginbase)[0]
			if site['enabled'] == False:
				logger.info("\tcalling UpdateSite(%s, enabled=True)" % loginbase)
				if not isSiteExempt(loginbase):
					api.UpdateSite(auth.auth, loginbase, {'enabled': True})
	except Exception, exc:
		print "ERROR: enableSiteSliceCreation:  %s" % exc
		logger.info("ERROR: enableSiteSliceCreation:  %s" % exc)

def enableSliceCreation(nodename):
        loginbase = siteId(nodename)
        enableSiteSliceCreation(loginbase)

def areSlicesEnabled(site):

	try:
		slice_list = api.GetSlices(slices(site))
		if len(slice_list) == 0:
			return None
		for slice in slice_list:
			slice_id = slice['slice_id']
			l_attr = api.GetSliceTags({'slice_id': slice_id})
			for attr in l_attr:
				if "enabled" == attr['tagname'] and attr['value'] == "0":
					return False

	except Exception, exc:
		pass

	return True
	

def isSiteEnabled(site):
    try:
        site = api.GetSites(site)[0]
        return site['enabled']
    except:
        pass

    return True
    

def isTagCurrent(tags):
    if len(tags) > 0:
        for tag in tags:
            until = tag['value']
            if datetime.strptime(until, "%Y%m%d") > datetime.now():
                # NOTE: the 'exempt_until' time is beyond current time
                return True
    return False

def isPersonExempt(email):
    tags = api.GetPersonTags({'email' : email, 'tagname' : 'exempt_person_until'})
    return isTagCurrent(tags)

def isNodeExempt(hostname):
    tags = api.GetNodeTags({'hostname' : hostname, 'tagname' : 'exempt_node_until'})
    return isTagCurrent(tags)

def isSliceExempt(slicename):
    tags = api.GetSliceTags({'name' : slicename, 'tagname' : 'exempt_slice_until'})
    return isTagCurrent(tags)

def isSiteExempt(loginbase):
    tags = api.GetSiteTags({'login_base' : loginbase, 'tagname' : 'exempt_site_until'})
    return isTagCurrent(tags)

'''
Removes site's ability to create slices. Returns previous max_slices
'''
def removeSiteSliceCreation(loginbase):
	#print "removeSiteSliceCreation(%s)" % loginbase

	if isPendingSite(loginbase):
		msg = "INFO: removeSiteSliceCreation: Pending Site (%s)" % loginbase
		print msg
		logger.info(msg)
		return

	api = xmlrpclib.Server(auth.server, verbose=False)
	try:
		logger.info("Removing slice creation for site %s" % loginbase)
		if not debug:
			if not isSiteExempt(loginbase):
			    api.UpdateSite(auth.auth, loginbase, {'enabled': False})
	except Exception, exc:
		logger.info("removeSiteSliceCreation:  %s" % exc)

'''
Removes ability to create slices. Returns previous max_slices
'''
def removeSliceCreation(nodename):
        loginbase = siteId(nodename)
        removeSiteSliceCreation(loginbase)


'''
QED
'''
#def enableSliceCreation(nodename, maxslices):
#	api = xmlrpclib.Server(auth.server, verbose=False)
#	anon = {'AuthMethod': "anonymous"}
#	siteid = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
#	if len(siteid) == 1:
#		logger.info("Enabling slice creation for site %s" % siteId(nodename))
#		try:
#			if not debug:
#				api.AdmUpdateSite(auth.auth, siteid[0], {"max_slices" : maxslices})
#		except Exception, exc:
#			logger.info("API:  %s" % exc)
#	else:
#		logger.debug("Cant find site for %s.  Cannot enable creation." % nodename)

def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('logger - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	#print getpcu("kupl2.ittc.ku.edu")
	#print getpcu("planetlab1.cse.msu.edu")
	#print getpcu("alice.cs.princeton.edu")
	#print nodesDbg()
	#nodeBootState("alice.cs.princeton.edu", "boot")
	#freezeSite("alice.cs.princeton.edu")
	print removeSliceCreation("alice.cs.princeton.edu")
	#enableSliceCreation("alice.cs.princeton.edu", 1024)
	#print getSiteNodes("princeton")
	#print siteId("alice.cs.princeton.edu")
	#print nodePOD("alice.cs.princeton.edu")
	#print slices("princeton")

if __name__=="__main__":
	main() 
