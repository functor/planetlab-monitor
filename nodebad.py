#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta

from nodequery import verify,query_to_dict,node_select

from nodecommon import *

from monitor import config
from monitor.wrapper import plc,plccache
from monitor.const import MINUP
from monitor.database.info.model import  FindbadNodeRecord, HistoryNodeRecord

from monitor.model import *

api = plc.getAuthAPI()

round = 1
count = 0

def main(config):

	l_plcnodes = plccache.l_nodes
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

		pf = HistoryNodeRecord.findby_or_create(hostname=nodename)
		pf.last_checked = datetime.now()

		try:
			# Find the most recent record
			noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==nodename).order_by(FindbadNodeRecord.date_checked.desc()).first()
			#print "NODEREC: ", noderec.date_checked
		except:
			print "COULD NOT FIND %s" % nodename
			import traceback
			print traceback.print_exc()
			continue

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

	# NOTE: this commits all pending operations to the DB.  Do not remove, or
	# replace with another operations that also commits all pending ops, such
	# as session.commit() or flush() or something
	print HistoryNodeRecord.query.count()

	return True

if __name__ == '__main__':
	from monitor import parser as parsermodule
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
