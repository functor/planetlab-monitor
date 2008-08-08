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
try:
	import config
	debug = config.debug
except:
	debug = False
logger = logging.getLogger("monitor")
	
class Auth:
	def __init__(self):
		self.auth = {'AuthMethod': "anonymous"}

# NOTE: this host is used by default when there are no auth files.
XMLRPC_SERVER="https://boot.planet-lab.org/PLCAPI/"

# NOTE: by default, use anonymous access, but if auth files are 
#       configured, use them, with their auth definitions.
auth = Auth()
try:
	import monitorconfig
	auth.auth = {'Username' : monitorconfig.API_AUTH_USER,
	             'AuthMethod' : 'password',
				 'AuthString' : monitorconfig.API_AUTH_PASSWORD}
	auth.server = monitorconfig.API_SERVER
except:
	try:
		import auth
		auth.server = auth.plc
	except:
		auth = Auth()
		auth.server = XMLRPC_SERVER

api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)

class PLC:
	def __init__(self, auth, url):
		self.auth = auth
		self.url = url
		self.api = xmlrpclib.Server(self.url, verbose=False, allow_none=True)

	def __getattr__(self, name):
		method = getattr(self.api, name)
		if method is None:
			raise AssertionError("method does not exist")

		return lambda *params : method(self.auth, *params)

	def __repr__(self):
		return self.api.__repr__()

def getAPI(url):
	return xmlrpclib.Server(url, verbose=False, allow_none=True)

def getAuthAPI():
	return PLC(auth.auth, auth.server)

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
	api = xmlrpclib.Server(auth.server, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	site_id = api.GetNodes (anon, {"hostname": nodename}, ['site_id'])
	if len(site_id) == 1:
		loginbase = api.GetSites (anon, site_id[0], ["login_base"])
		return loginbase[0]['login_base']

'''
Returns list of slices for a site.
'''
def slices(loginbase):
	siteslices = []
	api = xmlrpclib.Server(auth.server, verbose=False)
	sliceids = api.GetSites (auth.auth, {"login_base" : loginbase}, ["slice_ids"])[0]['slice_ids']
	for slice in api.GetSlices(auth.auth, {"slice_id" : sliceids}, ["name"]):
		siteslices.append(slice['name'])
	return siteslices

'''
Returns dict of PCU info of a given node.
'''
def getpcu(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	nodeinfo = api.GetNodes(auth.auth, {"hostname": nodename}, ["pcu_ids", "ports"])[0]
	if nodeinfo['pcu_ids']:
		sitepcu = api.GetPCUs(auth.auth, nodeinfo['pcu_ids'])[0]
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
	nodenetworks = api.GetNodeNetworks(auth.auth, filter, None)
	return nodenetworks

def getNodes(filter=None, fields=None):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	nodes = api.GetNodes(auth.auth, filter, fields) 
			#['boot_state', 'hostname', 
			#'site_id', 'date_created', 'node_id', 'version', 'nodenetwork_ids',
			#'last_updated', 'peer_node_id', 'ssh_rsa_key' ])
	return nodes

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
def suspendSlices(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False)
	for slice in slices(siteId(nodename)):
		logger.info("Suspending slice %s" % slice)
		try:
			if not debug:
				api.AddSliceAttribute(auth.auth, slice, "enabled", "0")
		except Exception, exc:
			logger.info("suspendSlices:  %s" % exc)

def enableSlices(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	for slice in slices(siteId(nodename)):
		logger.info("Enabling slices %s" % slice)
		try:
			if not debug:
				slice_list = api.GetSlices(auth.auth, {'name': slice}, None)
				if len(slice_list) == 0:
					return
				slice_id = slice_list[0]['slice_id']
				l_attr = api.GetSliceAttributes(auth.auth, {'slice_id': slice_id}, None)
				for attr in l_attr:
					if "enabled" == attr['name'] and attr['value'] == "0":
						logger.info("Deleted enable=0 attribute from slice %s" % slice)
						api.DeleteSliceAttribute(auth.auth, attr['slice_attribute_id'])
		except Exception, exc:
			logger.info("enableSlices: %s" % exc)
			print "exception: %s" % exc

#I'm commenting this because this really should be a manual process.  
#'''
#Enable suspended site slices.
#'''
#def enableSlices(nodename, slicelist):
#	api = xmlrpclib.Server(auth.server, verbose=False)
#	for slice in  slices(siteId(nodename)):
#		logger.info("Suspending slice %s" % slice)
#		api.SliceAttributeAdd(auth.auth, slice, "plc_slice_state", {"state" : "suspended"})
#
def enableSliceCreation(nodename):
	api = xmlrpclib.Server(auth.server, verbose=False, allow_none=True)
	try:
		loginbase = siteId(nodename)
		logger.info("Enabling slice creation for site %s" % loginbase)
		if not debug:
			logger.info("\tcalling UpdateSite(%s, enabled=True)" % loginbase)
			api.UpdateSite(auth.auth, loginbase, {'enabled': True})
	except Exception, exc:
		print "ERROR: enableSliceCreation:  %s" % exc
		logger.info("ERROR: enableSliceCreation:  %s" % exc)

'''
Removes ability to create slices. Returns previous max_slices
'''
def removeSliceCreation(nodename):
	print "removeSliceCreation(%s)" % nodename
	api = xmlrpclib.Server(auth.server, verbose=False)
	try:
		loginbase = siteId(nodename)
		#numslices = api.GetSites(auth.auth, {"login_base": loginbase}, 
		#		["max_slices"])[0]['max_slices']
		logger.info("Removing slice creation for site %s" % loginbase)
		if not debug:
			#api.UpdateSite(auth.auth, loginbase, {'max_slices': 0})
			api.UpdateSite(auth.auth, loginbase, {'enabled': False})
	except Exception, exc:
		logger.info("removeSliceCreation:  %s" % exc)

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
