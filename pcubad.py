#!/usr/bin/python

import os
import sys
import string
import time
import sets
from datetime import datetime,timedelta

from monitor import database
from monitor import reboot
from monitor import parser as parsermodule
from monitor import config
from monitor.database.info.model import HistoryPCURecord, FindbadPCURecord
from monitor.database.dborm import mon_session as session
from monitor.wrapper import plc,plccache
from monitor.const import MINUP

from monitor.common import *
from nodequery import verify,query_to_dict,node_select
from monitor.model import *

api = plc.getAuthAPI()

def main():
	main2(config)

def main2(config):

	l_plcpcus = plccache.l_pcus 

	l_pcus = None
	if config.site is not None:
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['pcu_ids'])
		pcus = []
		for node in l_nodes:
			pcus += node['pcu_ids']
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]
	elif config.pcu:
		for pcu in l_plcpcus:
			if ( pcu['hostname'] is not None and config.pcu in pcu['hostname'] ) or \
			   ( pcu['ip'] is not None and config.pcu in pcu['ip'] ):
				l_pcus = [pcu['pcu_id']]
		if not l_pcus:
			print "ERROR: could not find pcu %s" % config.pcu
			sys.exit(1)
	else:
		l_pcus = [pcu['pcu_id'] for pcu in l_plcpcus]
	
	checkAndRecordState(l_pcus, l_plcpcus)

hn2lb = plccache.plcdb_hn2lb

def check_pcu_state(rec, pcu):

	pcu_state = rec.reboot_trial_status

	if ( pcu_state == 'NetDown' or pcu_state == 'Not_Run' or not ( pcu_state == 0 or pcu_state == "0" ) ) and \
			( pcu.status == 'online' or pcu.status == 'good' ):
		print "changed status from %s to offline" % pcu.status
		pcu.status = 'offline'
		pcu.last_changed = datetime.now()

	if ( pcu_state == 0 or pcu_state == "0" ) and changed_lessthan(pcu.last_changed, 0.5) and pcu.status != 'online':
		print "changed status from %s to online" % pcu.status
		pcu.status = 'online'
		pcu.last_changed = datetime.now()

	if pcu.status == 'online' and changed_greaterthan(pcu.last_changed, 0.5):
		#send thank you notice, or on-line notice.
		print "changed status from %s to good" % pcu.status
		pcu.status = 'good'
		# NOTE: do not reset last_changed, or you lose how long it's been up.

	if pcu.status == 'offline' and changed_greaterthan(pcu.last_changed, 2):
		# send down pcu notice
		print "changed status from %s to down" % pcu.status
		pcu.status = 'down'
		pcu.last_changed = datetime.now()

	if ( pcu.status == 'offline' or pcu.status == 'down' ) and changed_greaterthan(pcu.last_changed, 2*30):
		print "changed status from %s to down" % pcu.status
		pcu.status = 'down'
		pcu.last_changed = datetime.now()

def checkAndRecordState(l_pcus, l_plcpcus):
	count = 0
	for pcuname in l_pcus:

		d_pcu = None
		for pcu in l_plcpcus:
			if pcu['pcu_id'] == pcuname:
				d_pcu = pcu
				break
		if not d_pcu:
			continue

		pcuhist = HistoryPCURecord.findby_or_create(plc_pcuid=d_pcu['pcu_id'], 
									if_new_set={'status' : 'offline', 
												'last_changed' : datetime.now()})
		pcuhist.last_checked = datetime.now()

		try:
			# Find the most recent record
			pcurec = FindbadPCURecord.query.filter(FindbadPCURecord.plc_pcuid==pcuname).order_by(FindbadPCURecord.date_checked.desc()).first()
		except:
			print "COULD NOT FIND FB record for %s" % reboot.pcu_name(d_pcu)
			import traceback
			print traceback.print_exc()
			# don't have the info to create a new entry right now, so continue.
			continue 

		if not pcurec:
			print "none object for pcu %s"% reboot.pcu_name(d_pcu)
			continue

		check_pcu_state(pcurec, pcuhist)

		count += 1
		print "%d %35s %s since(%s)" % (count, reboot.pcu_name(d_pcu), pcuhist.status, diff_time(time.mktime(pcuhist.last_changed.timetuple())))

	# NOTE: this commits all pending operations to the DB.  Do not remove, or
	# replace with another operations that also commits all pending ops, such
	# as session.commit() or flush() or something
	session.flush()
	print HistoryPCURecord.query.count()

	return True

if __name__ == '__main__':
	parser = parsermodule.getParser()
	parser.set_defaults(filename=None, pcu=None, site=None, pcuselect=False, pcugroup=None, cachepcus=False)
	parser.add_option("", "--pcu", dest="pcu", metavar="hostname", 
						help="Provide a single pcu to operate on")
	parser.add_option("", "--site", dest="site", metavar="sitename", 
						help="Provide a single sitename to operate on")
	parser.add_option("", "--pculist", dest="pculist", metavar="file.list", 
						help="Provide a list of files to operate on")

	config = parsermodule.parse_args(parser)

	try:
		main2(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
