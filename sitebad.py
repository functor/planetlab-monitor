#!/usr/bin/python

import os
import sys
import string
import time


import database
import comon
import threadpool
import syncplcdb
from nodequery import verify,query_to_dict,node_select
from datetime import datetime,timedelta
import config

from sqlobject import connectionForURI,sqlhub
connection = connectionForURI(config.sqlobjecturi)
sqlhub.processConnection = connection
from infovacuum.model.findbadrecord import *
from infovacuum.model.historyrecord import *

import plc
api = plc.getAuthAPI()
from unified_model import *
from const import MINUP

def main(config):

	l_nodes = syncplcdb.create_plcdb()
	l_plcsites = database.dbLoad("l_plcsites")

	if config.site:
		l_sites = [config.site]
	else:
		l_sites = [site['login_base'] for site in l_plcsites]
	
	checkAndRecordState(l_sites, l_plcsites)

def getnodesup(nodelist):
	up = 0
	for node in nodelist:
		try:
			noderec = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname==node['hostname'], 
											   orderBy='date_checked').reversed()[0]
			if noderec.observed_status == "BOOT":
				up = up + 1
		except:
			pass
	return up

def checkAndRecordState(l_sites, l_plcsites):
	count = 0
	lb2hn = database.dbLoad("plcdb_lb2hn")
	for sitename in l_sites:
		d_site = None
		for site in l_plcsites:
			if site['login_base'] == sitename:
				d_site = site
				break
		if not d_site:
			continue

		if sitename in lb2hn:
			try:
				pf = HistorySiteRecord.by_loginbase(sitename)
			except:
				pf = HistorySiteRecord(loginbase=sitename)

			pf.last_checked = datetime.now()

			pf.slices_used = len(d_site['slice_ids'])
			pf.nodes_total = len(lb2hn[sitename])
			pf.nodes_up = getnodesup(lb2hn[sitename])

			if pf.nodes_up >= MINUP:
				if pf.status != "good": pf.last_changed = datetime.now()
				pf.status = "good"
			else:
				if pf.status != "down": pf.last_changed = datetime.now()
				pf.status = "down"

			count += 1
			print "%d %15s slices(%2s) nodes(%2s) up(%2s) %s" % (count, sitename, pf.slices_used, 
											pf.nodes_total, pf.nodes_up, pf.status)

	return True

if __name__ == '__main__':
	import parser as parsermodule

	parser = parsermodule.getParser()
	parser.set_defaults(filename=None, node=None, site=None, 
						nodeselect=False, nodegroup=None, cachenodes=False)

	parser.add_option("", "--site", dest="site", metavar="login_base", 
						help="Provide a single site to operate on")
	parser.add_option("", "--sitelist", dest="sitelist", metavar="file.list", 
						help="Provide a list of files to operate on")

	config = parsermodule.parse_args(parser)

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
