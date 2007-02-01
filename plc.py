#!/bin/env python
#
# Helper functions that minipulate the PLC api.
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Copyright (C) 2006, 2007 The Trustees of Princeton University
#
# $Id: plc.py,v 1.2 2007/01/24 19:29:44 mef Exp $
#

from emailTxt import *
import xml, xmlrpclib
import logging
import time
import config
import getpass, getopt
import sys

logger = logging.getLogger("monitor")
XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'
api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
anon = None
auth = None

def nodesDbg(argv):
	"""Returns list of nodes in dbg as reported by PLC"""

	global api, anon, auth
	dbgNodes = []
	allnodes = api.AnonAdmGetNodes(anon, [], ['hostname','boot_state'])
	for node in allnodes:
		if node['boot_state'] == 'dbg': dbgNodes.append(node['hostname'])
	logger.info("%s nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes


def siteId(argv):
	"""Returns loginbase for given nodename"""

	global api, anon, auth
	nodename = argv[0]
	site_id = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	if len(site_id) == 1:
		loginbase = api.AnonAdmGetSites (anon, site_id, ["login_base"])
		return loginbase[0]['login_base']

def slices(argv):
	"""Returns list of slices for a site."""

	global api, anon, auth
	loginbase = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)
	return api.SliceListNames (auth, loginbase)

def getpcu(argv):
	"""Returns dict of PCU info of a given node."""

	global api, anon, auth
	nodename = argv[0].lower()
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	nodes = []
	site_id = api.AnonAdmQuerySite (anon, {"node_hostname": nodename})
	if len(site_id) == 1:
		try:
			sitepcus = api.AdmGetSitePowerControlUnits(auth, site_id[0])
			for sitepcu in sitepcus:
				sitepcuports = api.AdmGetPowerControlUnitNodes(auth, sitepcu['pcu_id'])
				for sitepcuport in sitepcuports:
					node_id = [sitepcuport['node_id']]
					node = api.AnonAdmGetNodes(anon,node_id,["hostname"])
					if len(node)==0:
						continue
					node = node[0]
					hostname = node['hostname'].lower()
					if hostname == nodename:
						sitepcu['port_number']=sitepcuport['port_number']
						return sitepcu

		except Exception, err:
			logger.debug("getpcu: %s" % err)
			return
	else:
		logger.info("Cant find site for %s" % nodename)


def getSiteNodes(argv):
	"""Returns all site nodes for site id (loginbase)."""
	global api, anon, auth
	loginbase = argv[0]
	nodelist = []
	try:
		site_id = api.AnonAdmQuerySite(anon, {'site_loginbase': "%s" % loginbase})
		node_ids = api.AnonAdmGetSiteNodes(anon, site_id)
		for node in api.AnonAdmGetNodes(anon, node_ids["%s" % site_id[0]], ["hostname"]):
			nodelist.append(node['hostname'])
	except Exception, exc:
		logger.info("getSiteNodes:  %s" % exc)
	nodelist.sort()
	return nodelist

def nodeBootState(argv):
	"""Sets boot state of a node."""

	global api, anon, auth
	if len(argv) <> 2:
		printUsage("not enough arguments")
		sys.exit(1)
		
	nodename = argv[0]
	state = argv[1]
	
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node_id = api.AnonAdmQueryNode(anon, {'node_hostname' : nodename})
	if len(node_id) == 1:
		logger.info("Setting node %s to %s" %(nodename, state))
		try:
			if not config.debug:
				api.AdmUpdateNode(auth, node_id[0], {'boot_state': state})
		except Exception, exc:
			logger.info("nodeBootState:  %s" % exc)
	else:
		logger.info("Cant find node %s to toggle boot state" % nodename)

def nodePOD(argv):
	"""Sends Ping Of Death to node."""

	global api, anon, auth
	nodename = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node_id = api.AnonAdmQueryNode(anon, {'node_hostname' : nodename})
	if len(node_id) == 1:
		logger.info("Sending POD to %s" % nodename)
		try:
			if not config.debug:
				api.AdmRebootNode(auth, node_id[0])
		except Exception, exc:
			logger.info("nodePOD:  %s" % exc)
	else:
		logger.info("Cant find node %s to send POD." % nodename)

def suspendSlices(argv):
	"""Freeze all site slices."""

	global api, anon, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	if argv[0].find(".") <> -1: siteslices = slices([siteId(argv)])
	else: siteslices = slices(argv)

	for slice in siteslices:
		logger.info("Suspending slice %s" % slice)
		try:
			if not config.debug:
				api.SliceAttributeAdd(auth, slice, "plc_slice_state", 
				{"state" : "suspended"})
		except Exception, exc:
			logger.info("suspendSlices:  %s" % exc)


def enableSlices(argv):
	"""Enable suspended site slices."""

	global api, anon, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)

	if argv[0].find(".") <> -1: siteslices = slices([siteId(argv)])
	else: siteslices = slices(argv)

	for slice in siteslices:
		logger.info("unfreezing slice %s" % slice)
		api.SliceAttributeDelete(auth, slice, "plc_slice_state")


def removeSliceCreation(argv):
	"""Removes ability to create slices. Returns previous max_slices"""

	global api, anon, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	name = argv[0]
	if name.find(".") <> -1:
		siteid = api.AnonAdmQuerySite (anon, {"node_hostname": name})
		loginbase = siteId(name)
	else:
		siteid = api.AnonAdmQuerySite (anon, {"site_loginbase": name})		
		loginbase = name

	numslices = api.AdmGetSites(auth, siteid, ["max_slices"])[0]['max_slices']
	if len(siteid) == 1:
		logger.info("Removing slice creation for site %s" % loginbase)
		try:
			if not config.debug:
				api.AdmUpdateSite(auth, siteid[0], {'max_slices': 0})
			return numslices
		except Exception, exc:
			logger.info("removeSliceCreation:  %s" % exc)
	else:
		logger.debug("Cant find site for %s.  Cannot revoke creation." % loginbase)

def enableSliceCreation(argv):
	"""QED"""

	global api, anon, auth
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	if len(argv) <= 2:
		printUsage("requires maxslice arg")
		sys.exit(1)

	maxslices = int(argv[1])
	name = argv[0]
	if name.find(".") <> -1:
		siteid = api.AnonAdmQuerySite (anon, {"node_hostname": name})
		loginbase = siteId(name)
	else:
		siteid = api.AnonAdmQuerySite (anon, {"site_loginbase": name})		
		loginbase = name

	if len(siteid) == 1:
		logger.info("Enabling slice creation for site %s" % loginbase)
		try:
			if not config.debug:
				api.AdmUpdateSite(auth, siteid[0], {"max_slices" : maxslices})
		except Exception, exc:
			logger.info("API:  %s" % exc)
	else:
		logger.debug("Cant find site for %s.  Cannot enable creation." % loginbase)



USAGE = """
Usage: %s [-u user] [-p password] [-r role] CMD

Options:
-u      PLC account username
-p      PLC account password
-r      PLC account role
-h      This message
""" % sys.argv[0]

def printUsage(error = None):
	global funclist
	if error <> None:
		print "%s %s" %(sys.argv[0],error)
	print USAGE
	print "CMD:"
	for name,function in funclist:
		print "%20s\t%20s" % (name, function.__doc__)
	
def main():
	global api, auth, anon

	anon = {"AuthMethod":"anonymous"}
	auth = None
	user = None
	password = None
	role = 'admin'

	(opts, argv) = getopt.getopt(sys.argv[1:], "u:p:r:h")
	if len(argv)==0:
		printUsage()
		sys.exit(1)

	for (opt, optval) in opts:
		if opt == '-u':
			user = optval
		elif opt == '-p':
			password = optval
		elif opt == '-r':
			role = optval
		elif opt == '-h':
			print USAGE
			sys.exit(0)

	if user <> None:
		if password is None:
			try:
				password = getpass.getpass()
			except (EOFError, KeyboardInterrupt):
				print( "" )
				sys.exit(1)
		auth = {}
		auth['Username'] = user
		auth['AuthMethod'] = "password"
		auth['AuthString'] = password
		auth['Role'] = role

	cmd = functbl.get(argv[0], None)
	if cmd is None:
		printUsage()
		sys.exit(1)

	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('logger - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	result = cmd(argv[1:])
	print result

funclist = (("nodesDbg",nodesDbg),
	    ("siteId", siteId),
	    ("slices", slices),
	    ("pcu", getpcu),
	    ("siteNodes", getSiteNodes),
	    ("nodeBootState", nodeBootState),
	    ("nodePOD", nodePOD),
	    ("freezeSlices", suspendSlices),
	    ("unfreezeSlices", enableSlices),
	    ("disableSliceCreation",removeSliceCreation),
	    ("enableSliceCreation", enableSliceCreation))

functbl = {}
for f in funclist:
	functbl[f[0]]=f[1]

if __name__=="__main__":
	import reboot
	main() 
