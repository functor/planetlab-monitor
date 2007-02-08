#!/bin/env python
#
# Helper functions that minipulate the PLC api.
# 
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
# Copyright (C) 2006, 2007 The Trustees of Princeton University
#
# $Id: plc.py,v 1.6 2007/02/08 19:59:03 mef Exp $
#

from emailTxt import *
import xml, xmlrpclib
import logging
import time
import config
import getpass, getopt
import sys

logger = logging.getLogger("monitor")
XMLRPC_SERVER = 'https://www2.planet-lab.org/PLCAPI/'
api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False, allow_none = True)
auth = None

def nodesDbg(argv):
	"""Returns list of nodes in dbg as reported by PLC"""

	global api, auth
	dbgNodes = []
	allnodes = api.GetNodes(auth, None, ['hostname','boot_state'])
	for node in allnodes:
		if node['boot_state'] == 'dbg': dbgNodes.append(node['hostname'])
	logger.info("%d nodes in debug according to PLC." %len(dbgNodes))
	return dbgNodes


def siteId(argv):
	"""Returns loginbase for given nodename"""

	global api, auth
	nodename = argv[0]
	site_ids = api.GetNodes(auth, [nodename], ['site_id'])
	if len(site_ids) == 1:
		site_id = [site_ids[0]['site_id']]
		loginbase = api.GetSites (auth, site_id, ["login_base"])
		return loginbase[0]['login_base']

def slices(argv):
	"""Returns list of slices for a site."""

	global api, anon, auth
	if len(argv) < 1:
		printUsage("not enough arguments; please provide loginbase")
		sys.exit(1)

	loginbase = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	def fast():
		slices = api.GetSlices (auth, {'name':"%s_*"%loginbase})
		return slices

	def slow():
		results = []
		slice_ids = api.GetSites(auth,{'login_base':loginbase},['slice_ids'])
		if len(slice_ids)==1:
			slice_ids=slice_ids[0]
			slice_ids=slice_ids['slice_ids']
			slices = api.GetSlices(auth,slice_ids,['name'])
			results = map(lambda x: x['name'],slices)
		return results

	return slow()

def getpcu(argv):
	"""Returns dict of PCU info of a given node."""

	global api, anon, auth
	nodename = argv[0].lower()
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	pcus = api.GetNodes(auth, [nodename], ['pcu_ids'])
	if len(pcus):
		pcus = map(lambda x: x['pcu_ids'],pcus)[0]
		nodepcus = api.GetPCUs(auth,pcus)
	else:
		nodepcus = []
	return nodepcus


def getSiteNodes(argv):
	"""Returns all site nodes for site id (loginbase)."""
	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments; please provide loginbase")
		sys.exit(1)

	loginbase = argv[0]
	nodelist = []
	site_ids = api.GetSites(auth, {'login_base': "%s" % loginbase}, ['node_ids'])
	if len(site_ids) == 1:
		node_ids = site_ids[0]['node_ids']
		nodes = api.GetNodes(auth,node_ids,['hostname'])
		nodelist = map(lambda x: x['hostname'], nodes)
	elif len(site_ids) == 0:
		logger.info("getSiteNodes: can't find site %s" %loginbase)	      
	nodelist.sort()
	return nodelist

def renewAllSlices (argv):
	"""Sets the expiration date of all slices to given date"""
	global api, auth

	newexp = argv[0]
	# convert time string using fmt "%B %d %Y" to epoch integer
	try:
		newexp = int(time.mktime(time.strptime(newexp,"%B %d %Y")))
	except ValueError, e:
		errormsg = """Expecting date to be in Month Day Year
  e.g., April 7 2007
  new expiration date provided %s""" % newexp
		printUsage(errormsg)
		sys.exit(1)
		
	slices = api.GetSlices(auth)
	for slice in slices:
		name = slice['name']
		exp = int(slice['expires'])
		olddate = time.asctime(time.localtime(exp))
		slice_attributes = api.GetSliceAttributes(auth,slice['slice_attribute_ids'])
		for slice_attribute in slice_attributes:
			if slice_attribute['name'] == "enabled":
				print "%s is suspended" % name
		continue
		if exp < newexp:
			newdate = time.asctime(time.localtime(newexp))
			ret = api.SliceRenew(auth,name,newexp)
			if ret == 0:
				print "failed to renew %s" %name

def nodeBootState(argv):
	"""Sets boot state of a node."""

	global api, anon, auth
	if len(argv) < 1:
		printUsage("not enough arguments")
		sys.exit(1)
		
	if len(argv) >=1:
		nodename = argv[0]
	if len(argv) >=2:
		state = argv[1]

	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node = api.GetNodes(auth, [nodename], ['node_id','boot_state'])
	if len(node) == 1:
		node = node[0]
		try:
			logger.info("%s boot_state=%s" %(nodename, node['boot_state']))
			if len(argv) >=2 and not config.debug:
				logger.info("Setting node %s boot_state=%s" %(nodename, state))
				node_id = node['node_id']
				api.UpdateNode(auth, node_id, {'boot_state': state})
		except Exception, exc:
			logger.info("nodeBootState:  %s" % exc)
	else:
		logger.info("Cant find node %s to toggle boot state" % nodename)

def nodePOD(argv):
	"""Sends Ping Of Death to node."""

	global api, auth
	if len(argv) < 1:
		printUsage("not enough arguments")
		sys.exit(1)
		
	nodename = argv[0]
	if auth is None:
		printUsage("requires admin privs")
		sys.exit(1)

	node = api.GetNodes(auth, [nodename], ['node_id'])
	if len(node) == 1:
		node = node[0]
		logger.info("Sending POD to %s" % nodename)
		try:
			if not config.debug:
				api.RebootNode(auth, node['node_id'])
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

	if len(argv) < 2:
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
	if result <> None:
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
	    ("enableSliceCreation", enableSliceCreation),
	    ("renewAllSlices", renewAllSlices))

functbl = {}
for f in funclist:
	functbl[f[0]]=f[1]

if __name__=="__main__":
	import reboot
	main() 
