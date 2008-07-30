#!/usr/bin/python

import os
import sys
import string
import time


import soltesz
import comon
import threadpool
import syncplcdb
from nodequery import verify,query_to_dict,node_select

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)
from unified_model import *
from monitor_policy import MINUP

round = 1
externalState = {'round': round, 'sites': {}}
count = 0

def main(config):
	global externalState
	externalState = soltesz.if_cached_else(1, config.dbname, lambda : externalState) 
	if config.increment:
		# update global round number to force refreshes across all nodes
		externalState['round'] += 1

	l_nodes = syncplcdb.create_plcdb()
	l_plcsites = soltesz.dbLoad("l_plcsites")

	if config.site:
		l_sites = [config.site]
	else:
		l_sites = [site['login_base'] for site in l_plcsites]
	
	checkAndRecordState(l_sites, l_plcsites)

def checkAndRecordState(l_sites, l_plcsites):
	global externalState
	global count
	global_round = externalState['round']

	for sitename in l_sites:
		if sitename not in externalState['sites']:
			externalState['sites'][sitename] = {'round': 0, 'values': []}

		site_round   = externalState['sites'][sitename]['round']
		if site_round < global_round:
			# do work
			values = collectStatusAndState(sitename, l_plcsites)
			global_round = externalState['round']
			externalState['sites'][sitename]['values'] = values
			externalState['sites'][sitename]['round'] = global_round
		else:
			count += 1

		if count % 20 == 0:
			soltesz.dbDump(config.dbname, externalState)

	soltesz.dbDump(config.dbname, externalState)

fb = soltesz.dbLoad('findbad')
lb2hn = soltesz.dbLoad("plcdb_lb2hn")

def getnodesup(nodelist):
	up = 0
	for node in nodelist:
		if node['hostname'] in fb['nodes'].keys():
			try:
				if fb['nodes'][node['hostname']]['values']['state'] == "BOOT":
					up = up + 1
			except:
				pass
	return up

def collectStatusAndState(sitename, l_plcsites):
	global count

	d_site = None
	for site in l_plcsites:
		if site['login_base'] == sitename:
			d_site = site
			break
	if not d_site:
		return None

	if sitename in lb2hn:
		pf = PersistFlags(sitename, 1, db='site_persistflags')

		if not pf.checkattr('last_changed'):
			pf.last_changed = time.time()
		
		pf.last_checked = time.time()
		pf.nodes_total = len(lb2hn[sitename])
		pf.slices_used = len(d_site['slice_ids'])
		pf.nodes_up = getnodesup(lb2hn[sitename])
		if not pf.checkattr('status'):
			pf.status = "unknown"

		if pf.nodes_up >= MINUP:
			if pf.status != "good": pf.last_changed = time.time()
			pf.status = "good"
		else:
			if pf.status != "down": pf.last_changed = time.time()
			pf.status = "down"

		count += 1
		print "%d %15s slices(%2s) nodes(%2s) up(%2s) %s" % (count, sitename, pf.slices_used, 
										pf.nodes_total, pf.nodes_up, pf.status)
		# updated by other modules
		#pf.enabled = 
		#pf.suspended = 

		pf.save()

	return True

if __name__ == '__main__':
	from config import config
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(filename=None, node=None, site=None, nodeselect=False, nodegroup=None, 
						increment=False, dbname="sitebad", cachenodes=False)
	parser.add_option("", "--site", dest="site", metavar="login_base", 
						help="Provide a single site to operate on")
	parser.add_option("", "--sitelist", dest="sitelist", metavar="file.list", 
						help="Provide a list of files to operate on")

	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	config = config(parser)
	config.parse_args()

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		soltesz.dbDump(config.dbname, externalState)
		sys.exit(0)
