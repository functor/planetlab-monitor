#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta

from monitor import database
from monitor.pcu import reboot
from monitor import parser as parsermodule
from monitor import config
from monitor.database import HistoryPCURecord, FindbadPCURecord
from monitor.wrapper import plc,plccache
from monitor.const import MINUP

from nodecommon import *
from nodequery import verify,query_to_dict,node_select
from monitor.model import *

api = plc.getAuthAPI()

def main(config):

	#l_plcpcus = database.if_cached_else_refresh(1, 1, "pculist", lambda : plc.GetPCUs())
	l_plcpcus = plccache.l_pcus 

	l_pcus = None
	if config.pcu:
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

		pf = HistoryPCURecord.findby_or_create(plc_pcuid=d_pcu['pcu_id'])
		pf.last_checked = datetime.now()

		try:
			# Find the most recent record
			pcurec = FindbadPCURecord.query.filter(FindbadPCURecord.plc_pcuid==pcuname).order_by(FindbadPCURecord.date_checked.desc()).first()
			print "NODEREC: ", pcurec.date_checked
		except:
			print "COULD NOT FIND FB record for %s" % reboot.pcu_name(pcu)
			import traceback
			print traceback.print_exc()
			# don't have the info to create a new entry right now, so continue.
			continue 

		pcu_state      = pcurec.reboot_trial_status
		current_state = pcu_state

		if current_state == 0 or current_state == "0":
			if pf.status != "good": 
				pf.last_changed = datetime.now() 
				pf.status = "good"
		elif current_state == 'NetDown':
			if pf.status != "netdown": 
				pf.last_changed = datetime.now()
				pf.status = "netdown"
		elif current_state == 'Not_Run':
			if pf.status != "badconfig": 
				pf.last_changed = datetime.now()
				pf.status = "badconfig"
		else:
			if pf.status != "error": 
				pf.last_changed = datetime.now()
				pf.status = "error"

		count += 1
		print "%d %35s %s since(%s)" % (count, reboot.pcu_name(d_pcu), pf.status, diff_time(time.mktime(pf.last_changed.timetuple())))

	# NOTE: this commits all pending operations to the DB.  Do not remove, or
	# replace with another operations that also commits all pending ops, such
	# as session.commit() or flush() or something
	print HistoryPCURecord.query.count()

	return True

if __name__ == '__main__':
	parser = parsermodule.getParser()
	parser.set_defaults(filename=None, pcu=None, pcuselect=False, pcugroup=None, cachepcus=False)
	parser.add_option("", "--pcu", dest="pcu", metavar="hostname", 
						help="Provide a single pcu to operate on")
	parser.add_option("", "--pculist", dest="pculist", metavar="file.list", 
						help="Provide a list of files to operate on")

	config = parsermodule.parse_args(parser)

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		sys.exit(0)
