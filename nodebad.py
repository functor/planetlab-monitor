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
		boot_state = rec.plc_node_stats['boot_state']
		last_contact = rec.plc_node_stats['last_contact']
	else:
		boot_state = "unknown"
		last_contact = None

	if node_state == 'DOWN' and ( node.status == 'online' or node.status == 'good' ):
		print "changed status from %s to offline" % node.status
		node.status = 'offline'
		node.last_changed = datetime.now()

	if node_state == 'BOOT' and changed_lessthan(node.last_changed, 0.5) and node.status != 'online':
		print "changed status from %s to online" % node.status
		node.status = 'online'
		node.last_changed = datetime.now()

	if node.status == 'online' and changed_greaterthan(node.last_changed, 0.5):
		#send thank you notice, or on-line notice.
		print "changed status from %s to good" % node.status
		node.status = 'good'
		# NOTE: do not reset last_changed, or you lose how long it's been up.

	#if node.status == 'offline' and changed_greaterthan(node.last_changed, 1): #  and pcu.status == 'good' 
	#	# attempt reboots
	#	pass
	#if node.status == 'offline' and changed_greaterthan(node.last_changed, 1.5): # and node.has_pcu
	#	# send PCU failure message
	#	pass

	if node.status == 'offline' and changed_greaterthan(node.last_changed, 2):
		print "changed status from %s to down" % node.status
		# send down node notice
		node.status = 'down'
		node.last_changed = datetime.now()

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
			noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==nodename).order_by(FindbadNodeRecord.date_checked.desc()).first()
		except:
			print "COULD NOT FIND %s" % nodename
			import traceback
			print traceback.print_exc()
			continue

		if not noderec:
			print "none object for %s"% nodename
			continue

		check_node_state(noderec, nodehist)

		count += 1
		print "%d %35s %s since(%s)" % (count, nodename, nodehist.status, diff_time(time.mktime(nodehist.last_changed.timetuple())))

	# NOTE: this commits all pending operations to the DB.  Do not remove, or
	# replace with another operations that also commits all pending ops, such
	# as session.commit() or flush() or something
	session.flush()
	print HistoryNodeRecord.query.count()

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
