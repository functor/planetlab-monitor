#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta

from monitor import database
from monitor import parser as parsermodule
from monitor import config
from monitor.database.info.model import HistorySiteRecord, FindbadNodeRecord, session
from monitor.wrapper import plc, plccache
from monitor.const import MINUP

from monitor.common import *
from nodequery import verify,query_to_dict,node_select
from monitor.model import *

api = plc.getAuthAPI()
def main():
	main2(config)

def main2(config):

	l_nodes = plccache.l_nodes
	l_plcsites = plccache.l_sites

	if config.site:
		l_sites = [config.site]
	elif config.sitelist:
		site_list = config.sitelist.split(',')
		l_sites = site_list
	else:
		l_sites = [site['login_base'] for site in l_plcsites]
	
	checkAndRecordState(l_sites, l_plcsites)

def getnewsite(nodelist):
	new = True
	for node in nodelist:
		try:
			noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==node['hostname']).order_by(FindbadNodeRecord.date_checked.desc()).first()
			if noderec is not None and \
				noderec.plc_node_stats['last_contact'] != None:
				new = False
		except:
			import traceback
			print traceback.print_exc()
	return new

def getnodesup(nodelist):
	up = 0
	for node in nodelist:
		try:
			noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==node['hostname']).order_by(FindbadNodeRecord.date_checked.desc()).first()
			#noderec = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname==node['hostname'], 
			#								   orderBy='date_checked').reversed()[0]
			if noderec is not None and noderec.observed_status == "BOOT":
				up = up + 1
		except:
			import traceback
			print traceback.print_exc()
	return up

def checkAndRecordState(l_sites, l_plcsites):
	count = 0
	lb2hn = plccache.plcdb_lb2hn
	for sitename in l_sites:
		d_site = None
		for site in l_plcsites:
			if site['login_base'] == sitename:
				d_site = site
				break
		if not d_site:
			continue

		if sitename in lb2hn:
			pf = HistorySiteRecord.findby_or_create(loginbase=sitename)

			pf.last_checked = datetime.now()
			pf.slices_total = d_site['max_slices']
			pf.slices_used = len(d_site['slice_ids'])
			pf.nodes_total = len(lb2hn[sitename])
			pf.nodes_up = getnodesup(lb2hn[sitename])
			pf.new = getnewsite(lb2hn[sitename])
			pf.enabled = d_site['enabled']

			if pf.nodes_up >= MINUP:
				if pf.status != "good": pf.last_changed = datetime.now()
				pf.status = "good"
			else:
				if pf.status != "down": pf.last_changed = datetime.now()
				pf.status = "down"

			count += 1
			print "%d %15s slices(%2s) nodes(%2s) up(%2s) %s" % (count, sitename, pf.slices_used, 
											pf.nodes_total, pf.nodes_up, pf.status)
			pf.flush()

	print HistorySiteRecord.query.count()
	session.flush()

	return True

if __name__ == '__main__':
	from monitor import parser as parsermodule

	parser = parsermodule.getParser()
	parser.set_defaults(filename=None, node=None, site=None, 
						nodeselect=False, nodegroup=None, cachenodes=False)

	parser.add_option("", "--site", dest="site", metavar="login_base", 
						help="Provide a single site to operate on")
	parser.add_option("", "--sitelist", dest="sitelist", 
						help="Provide a list of sites separated by ','")

	config = parsermodule.parse_args(parser)

	try:
		main2(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
