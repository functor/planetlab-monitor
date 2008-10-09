#!/usr/bin/python

import os
import sys
import string
import time

from reboot import pcu_name

import database
import comon
import threadpool
import syncplcdb
from nodequery import verify,query_to_dict,node_select
import parser as parsermodule
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


def main(config):

	l_plcpcus = database.if_cached_else_refresh(1, 1, "pculist", lambda : plc.GetPCUs())

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

hn2lb = database.dbLoad("plcdb_hn2lb")

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

		try:
			pf = HistoryPCURecord.by_pcuid(d_pcu['pcu_id'])
		except:
			pf = HistoryPCURecord(plc_pcuid=pcuname)

		pf.last_checked = datetime.now()

		try:
			# Find the most recent record
			pcurec = FindbadPCURecord.select(FindbadPCURecord.q.plc_pcuid==pcuname, 
											   orderBy='date_checked').reversed()[0]
		except:
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
		print "%d %35s %s since(%s)" % (count, pcu_name(d_pcu), pf.status, diff_time(time.mktime(pf.last_changed.timetuple())))

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
