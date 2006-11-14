#
# plc.py
#
# Helper functions that minipulate the PLC api.
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu
#
# $Id: $
#

from emailTxt import *
import xml, xmlrpclib
import logging
import auth
import time
import config

logger = logging.getLogger("monitor")

XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'

'''
Returns list of nodes in dbg as reported by PLC
'''
def nodesDbg():
	dbgNodes = []
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	allnodes = api.AnonAdmGetNodes(anon, [], ['hostname','boot_state'])
	for node in allnodes:
		if node['boot_state'] == 'dbg': dbgNodes.append(node['hostname'])
	logger.info("%s nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes


'''
Returns loginbase for given nodename
'''
def siteId(nodename):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	site_id = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	if len(site_id) == 1:
		loginbase = api.AnonAdmGetSites (anon, site_id, ["login_base"])
		return loginbase[0]['login_base']

'''
Returns list of slices for a site.
'''
def slices(loginbase):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	return api.SliceListNames (auth.auth, loginbase)

'''
Returns dict of PCU info of a given node.
'''
def getpcu(nodename):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	nodes = []
	site_id = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	if len(site_id) == 1:
		# PCU uname, pw, etc
		try:
			sitepcu = api.AdmGetSitePowerControlUnits(auth.auth, site_id[0])[0]
			# returns node_id and port
			sitepcuports = api.AdmGetPowerControlUnitNodes(auth.auth, sitepcu['pcu_id'])
			# Joining feilds
			for nodeidports in sitepcuports:
				nodeidports.update(api.AnonAdmGetNodes(anon, 
				[nodeidports['node_id']], ["node_id", "hostname"])[0])
				nodes.append(nodeidports)

			# WHY THE FUCK DOES EVERY XMl+RPC RETURN A FUCKING ARRAY?????
			# FURTHER, WHY THE FUCK WOULD YOU RETURN A NODE-ID WHEN SANITY WOULD SUGGEST
			# FQDN???? /RANT
			for node in nodes:
				sitepcu[node['hostname']] = node['port_number']

			# Sanity Check.  Make sure the node is in the return, if not, barf.
			if nodename in sitepcu.keys():
				return sitepcu
			else:
				raise Exception
		except Exception, err:
			logger.debug("getpcu: %s" % err)
			return
	else:
		logger.info("Cant find site for %s" % nodename)


'''
Returns all site nodes for site id (loginbase).
'''
def getSiteNodes(loginbase):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	nodelist = []
	anon = {'AuthMethod': "anonymous"}
	try:
		site_id = api.AnonAdmQuerySite(anon, {'site_loginbase': "%s" % loginbase})
		node_ids = api.AnonAdmGetSiteNodes(anon, site_id)
		for node in api.AnonAdmGetNodes(anon, node_ids["%s" % site_id[0]], ["hostname"]):
			nodelist.append(node['hostname'])
	except Exception, exc:
		logger.info("getSiteNodes:  %s" % exc)
	return nodelist

'''
Sets boot state of a node.
'''
def nodeBootState(nodename, state):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	node_id = api.AnonAdmQueryNode(anon, {'node_hostname' : nodename})
	if len(node_id) == 1:
		logger.info("Setting node %s to %s" %(nodename, state))
		try:
			if not config.debug:
				api.AdmUpdateNode(auth.auth, node_id[0], {'boot_state': state})
		except Exception, exc:
			logger.info("nodeBootState:  %s" % exc)
	else:
		logger.info("Cant find node %s to toggle boot state" % nodename)

'''
Sends Ping Of Death to node.
'''
def nodePOD(nodename):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	node_id = api.AnonAdmQueryNode(anon, {'node_hostname' : nodename})
	if len(node_id) == 1:
		logger.info("Sending POD to %s" % nodename)
		try:
			if not config.debug:
				api.AdmRebootNode(auth.auth, node_id[0])
		except Exception, exc:
			logger.info("nodePOD:  %s" % exc)
	else:
		logger.info("Cant find node %s to send POD." % nodename)

'''
Freeze all site slices.
'''
def suspendSlices(nodename):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	for slice in slices(siteId(nodename)):
		logger.info("Suspending slice %s" % slice)
		try:
			if not config.debug:
				api.SliceAttributeAdd(auth.auth, slice, "plc_slice_state", 
				{"state" : "suspended"})
		except Exception, exc:
			logger.info("suspendSlices:  %s" % exc)


#I'm commenting this because this really should be a manual process.  
#'''
#Enable suspended site slices.
#'''
#def enableSlices(nodename, slicelist):
#	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
#	for slice in  slices(siteId(nodename)):
#		logger.info("Suspending slice %s" % slice)
#		api.SliceAttributeAdd(auth.auth, slice, "plc_slice_state", {"state" : "suspended"})
#

'''
Removes ability to create slices. Returns previous max_slices
'''
def removeSliceCreation(nodename):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	siteid = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	numslices = api.AdmGetSites(auth.auth, siteid, ["max_slices"])[0]['max_slices']
	if len(siteid) == 1:
		logger.info("Removing slice creation for site %s" % siteId(nodename))
		try:
			if not config.debug:
				api.AdmUpdateSite(auth.auth, siteid[0], {'max_slices': 0})
			return numslices
		except Exception, exc:
			logger.info("removeSliceCreation:  %s" % exc)
	else:
		logger.debug("Cant find site for %s.  Cannot revoke creation." % nodename)

'''
QED
'''
def enableSliceCreation(nodename, maxslices):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	siteid = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	if len(siteid) == 1:
		logger.info("Enabling slice creation for site %s" % siteId(nodename))
		try:
			if not config.debug:
				api.AdmUpdateSite(auth.auth, siteid[0], {"max_slices" : maxslices})
		except Exception, exc:
			logger.info("API:  %s" % exc)
	else:
		logger.debug("Cant find site for %s.  Cannot enable creation." % nodename)

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
	#nodeBootState("alice.cs.princaeton.edu", "boot")
	#freezeSite("alice.cs.princeton.edu")
	#removeSliceCreation("alice.cs.princeton.edu")
	#enableSliceCreation("alice.cs.princeton.edu", 1024)
	print getSiteNodes("princeton")
	#print siteId("alice.cs.princeton.edu")
	#print nodePOD("planetlab5.warsaw.rd.tp.pl")

if __name__=="__main__":
	import reboot
	main() 
