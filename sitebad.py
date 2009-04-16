#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta

from monitor import database
from monitor import parser as parsermodule
from monitor import config
from monitor.database.info.model import HistorySiteRecord, HistoryNodeRecord, session, BlacklistRecord
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
	elif config.node:
		l_sites = [plccache.plcdb_hn2lb[config.node]]
	elif config.sitelist:
		site_list = config.sitelist.split(',')
		l_sites = site_list
	else:
		l_sites = [site['login_base'] for site in l_plcsites]
	
	checkAndRecordState(l_sites, l_plcsites)

def getnodesup(nodelist):
	# NOTE : assume that a blacklisted node is fine, since we're told not to
	# 		ignore it, no policy actions should be taken for it.
	up = 0
	for node in nodelist:
		try:
			# NOTE: adding a condition for nodehist.haspcu would include pcus
			# 		in the calculation
			nodehist = HistoryNodeRecord.findby_or_create(hostname=node['hostname'])
			nodebl   = BlacklistRecord.get_by(hostname=node['hostname'])
			if (nodehist is not None and nodehist.status != 'down') or \
				(nodebl is not None and not nodebl.expired()):
				up = up + 1
		except:
			import traceback
			email_exception(node['hostname'])
			print traceback.print_exc()
	return up

def check_site_state(rec, sitehist):

	if sitehist.new and sitehist.status not in ['new', 'online', 'good']:
		sitehist.status = 'new'
		sitehist.penalty_applied = True		# because new sites are disabled by default, i.e. have a penalty.
		sitehist.last_changed = datetime.now()

	if sitehist.nodes_up >= MINUP:

		if sitehist.status != 'online' and sitehist.status != 'good':
			sitehist.last_changed = datetime.now()

		if changed_lessthan(sitehist.last_changed, 0.5) and sitehist.status != 'online':
			print "changed status from %s to online" % sitehist.status
			sitehist.status = 'online'

		if changed_greaterthan(sitehist.last_changed, 0.5) and sitehist.status != 'good':
			print "changed status from %s to good" % sitehist.status
			sitehist.status = 'good'

	elif not sitehist.new:
	
		if sitehist.status != 'offline' and sitehist.status != 'down':
			sitehist.last_changed = datetime.now()

		if changed_lessthan(sitehist.last_changed, 0.5) and sitehist.status != 'offline':
			print "changed status from %s to offline" % sitehist.status
			sitehist.status = 'offline'

		if changed_greaterthan(sitehist.last_changed, 0.5) and sitehist.status != 'down':
			print "changed status from %s to down" % sitehist.status
			sitehist.status = 'down'

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
			sitehist = HistorySiteRecord.findby_or_create(loginbase=sitename,
												if_new_set={'status' : 'unknown', 
															'last_changed' : datetime.now(),
															'message_id': 0,
															'penalty_level' : 0})
			sitehist.last_checked = datetime.now()

			sitehist.slices_total = d_site['max_slices']
			sitehist.slices_used = len(d_site['slice_ids'])
			sitehist.nodes_total = len(lb2hn[sitename])
			if sitehist.message_id != 0:
				rtstatus = mailer.getTicketStatus(sitehist.message_id)
				sitehist.message_status = rtstatus['Status']
				sitehist.message_queue = rtstatus['Queue']
				sitehist.message_created = datetime.fromtimestamp(rtstatus['Created'])

			sitehist.nodes_up = getnodesup(lb2hn[sitename])
			sitehist.new = changed_lessthan(datetime.fromtimestamp(d_site['date_created']), 30) # created < 30 days ago
			sitehist.enabled = d_site['enabled']

			check_site_state(d_site, sitehist)

			count += 1
			print "%d %15s slices(%2s) nodes(%2s) notdown(%2s) %s" % (count, sitename, sitehist.slices_used, 
											sitehist.nodes_total, sitehist.nodes_up, sitehist.status)
			sitehist.flush()

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
