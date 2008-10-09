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
from nodecommon import *
from datetime import datetime,timedelta
import config

from sqlobject import connectionForURI,sqlhub
connection = connectionForURI(config.sqlobjecturi)
sqlhub.processConnection = connection
from infovacuum.model_findbadrecord import *
from infovacuum.model_historyrecord import *

import plc
api = plc.getAuthAPI()
from unified_model import *
from const import MINUP

round = 1
count = 0

def main(config):

	l_nodes = syncplcdb.create_plcdb()
	l_plcnodes = database.dbLoad("l_plcnodes")
	l_nodes = get_nodeset(config)
	
	checkAndRecordState(l_nodes, l_plcnodes)

def checkAndRecordState(l_nodes, l_plcnodes):
	global count

	for nodename in l_nodes:
		d_node = None
		for node in l_plcnodes:
			if node['hostname'] == nodename:
				d_node = node
				break
		if not d_node:
			continue

		try:
			pf = HistoryNodeRecord.by_hostname(nodename)
		except:
			pf = HistoryNodeRecord(hostname=nodename)

		pf.last_checked = datetime.now()

		try:
			# Find the most recent record
			noderec = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname==nodename, 
											   orderBy='date_checked').reversed()[0]
		except:
			# or create an empty one.
			noderec = FindbadNodeRecord(hostname=nodename)

		node_state = noderec.observed_status
		if noderec.plc_node_stats:
			boot_state = noderec.plc_node_stats['boot_state']
		else:
			boot_state = "unknown"

		if node_state == "BOOT":
			if pf.status != "good": 
				pf.last_changed = datetime.now()
				pf.status = "good"
		elif node_state == "DEBUG":
			if pf.status != boot_state: 
				pf.last_changed = datetime.now()
				pf.status = boot_state
		else:
			if pf.status != "down": 
				pf.last_changed = datetime.now()
				pf.status = "down"

		count += 1
		print "%d %35s %s since(%s)" % (count, nodename, pf.status, diff_time(time.mktime(pf.last_changed.timetuple())))

	return True

if __name__ == '__main__':
	import parser as parsermodule
	parser = parsermodule.getParser(['nodesets'])
	parser.set_defaults(filename=None, node=None, nodeselect=False, nodegroup=None, cachenodes=False)
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
