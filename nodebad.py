#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta

from nodequery import verify,query_to_dict,node_select

from monitor.common import *

from monitor import config
from monitor.wrapper import plc,plccache
from monitor.const import MINUP
from monitor.database.info.model import  FindbadNodeRecord, HistoryNodeRecord
from monitor.database.dborm import  mon_session as session

from monitor.model import *

api = plc.getAuthAPI()

round = 1
count = 0
def main():
	main2(config)

def main2(config):

	l_plcnodes = plccache.l_nodes
	l_nodes = get_nodeset(config)
	
	checkAndRecordState(l_nodes, l_plcnodes)

# Node states:

def check_node_state(rec, node):

	node_state = rec.observed_status
	if rec.plc_node_stats:
		print rec.plc_node_stats
		boot_state = rec.plc_node_stats['boot_state']
		last_contact = rec.plc_node_stats['last_contact']
	else:
		boot_state = "unknown"
		last_contact = None

	if boot_state == 'disable': boot_state = 'disabled'
	if boot_state == 'diag': 	boot_state = 'diagnose'

	if len(rec.plc_node_stats['pcu_ids']) > 0:
		node.haspcu = True
	else:
		node.haspcu = False

	# NOTE: 'DOWN' and 'DEBUG'  are temporary states, so only need
	# 			'translations' into the node.status state
	#		'BOOT' is a permanent state, but we want it to have a bit of
	#			hysteresis (less than 0.5 days)

	#################################################################
	# "Initialize" the findbad states into nodebad status if they are not already set

	if node_state == 'DOWN' and ( node.status != 'offline' and node.status != 'down' ) and boot_state != 'disabled' :
		print "changed status from %s to offline" % node.status
		node.status = 'offline'
		node.last_changed = datetime.now()

	if node_state == 'DEBUG' and node.status != 'monitordebug' and \
								 node.status != 'disabled' and \
								 node.status != 'diagnose':
		if boot_state != 'disabled' and boot_state != 'diagnose':

			print "changed status from %s to monitordebug" % (node.status)
			node.status = "monitordebug"
			node.last_changed = datetime.now()
		else:
			print "changed status from %s to %s" % (node.status, boot_state)
			node.status = boot_state
			node.last_changed = datetime.now()

	if node_state == 'BOOT' and node.status != 'online' and node.status != 'good':
		print "changed status from %s to online" % node.status
		node.status = 'online'
		node.last_changed = datetime.now()

	#################################################################
	# Switch temporary hystersis states into their 'firm' states.
	#	  online -> good		after half a day
	#	  offline -> down		after two days
	#	  monitordebug -> down  after 30 days
	#	  diagnose -> monitordebug after 60 days
	#	  disabled -> down		after 60 days

	if node.status == 'online' and changed_greaterthan(node.last_changed, 0.5):
		print "changed status from %s to good" % node.status
		node.status = 'good'
		# NOTE: do not reset last_changed, or you lose how long it's been up.

	if node.status == 'offline' and changed_greaterthan(node.last_changed, 2):
		print "changed status from %s to down" % node.status
		node.status = 'down'
		# NOTE: do not reset last_changed, or you lose how long it's been down.

	if node.status == 'monitordebug' and changed_greaterthan(node.last_changed, 30):
		print "changed status from %s to down" % node.status
		node.status = 'down'
		# NOTE: do not reset last_changed, or you lose how long it's been down.

	if node.status == 'diagnose' and changed_greaterthan(node.last_changed, 60):
		print "changed status from %s to down" % node.status
		# NOTE: change an admin mode back into monitordebug after two months.
		node.status = 'monitordebug'
		node.last_changed = datetime.now()

	# extreme cases of offline nodes
	if ( boot_state == 'disabled' or last_contact == None ) and \
			changed_greaterthan(node.last_changed, 2*30) and \
			node.status != 'down':
		print "changed status from %s to down" % node.status
		node.status = 'down'
		node.last_changed = datetime.now()

def checkAndRecordState(l_nodes, l_plcnodes):
	global count

	for nodename in l_nodes:

		nodehist = HistoryNodeRecord.findby_or_create(hostname=nodename, 
							if_new_set={'status' : 'offline', 
										'last_changed' : datetime.now()})
		nodehist.last_checked = datetime.now()

		try:
			# Find the most recent record
			noderec = FindbadNodeRecord.get_latest_by(hostname=nodename)
		except:
			print "COULD NOT FIND %s" % nodename
			import traceback
			email_exception()
			print traceback.print_exc()
			continue

		if not noderec:
			print "none object for %s"% nodename
			continue

		check_node_state(noderec, nodehist)

		count += 1
		print "%d %35s %s since(%s)" % (count, nodename, nodehist.status, diff_time(time.mktime(nodehist.last_changed.timetuple())))

	# NOTE: this commits all pending operations to the DB.  Do not remove. 
	session.flush()

	return True

if __name__ == '__main__':
	from monitor import parser as parsermodule
	parser = parsermodule.getParser(['nodesets'])
	parser.set_defaults(filename=None, node=None, nodeselect=False, nodegroup=None, cachenodes=False)
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

	try:
		main2(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
