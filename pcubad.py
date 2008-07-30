#!/usr/bin/python

import os
import sys
import string
import time

from reboot import pcu_name

import soltesz
import comon
import threadpool
import syncplcdb
from nodequery import verify,query_to_dict,node_select

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)
from unified_model import *
from monitor_policy import MINUP

round = 1
externalState = {'round': round, 'nodes': {}}
count = 0

def main(config):
	global externalState
	externalState = soltesz.if_cached_else(1, config.dbname, lambda : externalState) 
	if config.increment:
		# update global round number to force refreshes across all pcus
		externalState['round'] += 1

	l_plcpcus = soltesz.if_cached_else_refresh(1, 1, "pculist", lambda : plc.GetPCUs())

	l_pcu = None
	if config.pcu:
		for pcu in l_plcpcus:
			if pcu['hostname'] == config.pcu  or pcu['ip'] == config.pcu:
				l_pcus = [pcu['pcu_id']]
		if not l_pcu:
			print "ERROR: could not find pcu %s" % config.pcu
			sys.exit(1)
	else:
		l_pcus = [pcu['pcu_id'] for pcu in l_plcpcus]
	
	checkAndRecordState(l_pcus, l_plcpcus)

def checkAndRecordState(l_pcus, l_plcpcus):
	global externalState
	global count
	global_round = externalState['round']

	for pcuname in l_pcus:
		if pcuname not in externalState['nodes']:
			externalState['nodes'][pcuname] = {'round': 0, 'values': []}

		pcu_round   = externalState['nodes'][pcuname]['round']
		if pcu_round < global_round:
			# do work
			values = collectStatusAndState(pcuname, l_plcpcus)
			global_round = externalState['round']
			externalState['nodes'][pcuname]['values'] = values
			externalState['nodes'][pcuname]['round'] = global_round
		else:
			count += 1

		if count % 20 == 0:
			soltesz.dbDump(config.dbname, externalState)

	soltesz.dbDump(config.dbname, externalState)

fbpcu = soltesz.dbLoad('findbadpcus')
hn2lb = soltesz.dbLoad("plcdb_hn2lb")

def get(fb, path):
	indexes = path.split("/")
	values = fb
	for index in indexes:
		if index in values:
			values = values[index]
		else:
			return None
	return values

def collectStatusAndState(pcuname, l_plcpcus):
	global count

	d_pcu = None
	for pcu in l_plcpcus:
		if pcu['pcu_id'] == pcuname:
			d_pcu = pcu
			break
	if not d_pcu:
		return None

	pf = PersistFlags(pcuname, 1, db='pcu_persistflags')

	if not pf.checkattr('last_changed'):
		pf.last_changed = time.time()
		
	pf.last_checked = time.time()

	if not pf.checkattr('valid'):
		pf.valid = "unknown"
		pf.last_valid = 0

	if not pf.checkattr('status'):
		pf.status = "unknown"

	state_path     = "nodes/id_" + str(pcuname) + "/values/reboot"
	bootstate_path = "nodes/id_" + str(pcuname) + "/values/plcpcu/boot_state"

	current_state = get(fbpcu, state_path)
	if current_state == 0:
		if pf.status != "good": pf.last_changed = time.time()
		pf.status = "good"
	elif current_state == 'NetDown':
		if pf.status != "netdown": pf.last_changed = time.time()
		pf.status = "netdown"
	elif current_state == 'Not_Run':
		if pf.status != "badconfig": pf.last_changed = time.time()
		pf.status = "badconfig"
	else:
		if pf.status != "error": pf.last_changed = time.time()
		pf.status = "error"

	count += 1
	print "%d %35s %s since(%s)" % (count, pcu_name(d_pcu), pf.status, diff_time(pf.last_changed))
	# updated by other modules
	#pf.enabled = 
	#pf.suspended = 

	pf.save()

	return True

if __name__ == '__main__':
	from config import config
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(filename=None, pcu=None, pcuselect=False, pcugroup=None, 
						increment=False, dbname="pcubad", cachepcus=False)
	parser.add_option("", "--pcu", dest="pcu", metavar="hostname", 
						help="Provide a single pcu to operate on")
	parser.add_option("", "--pculist", dest="pculist", metavar="file.list", 
						help="Provide a list of files to operate on")

	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	config = config(parser)
	config.parse_args()

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		soltesz.dbDump(config.dbname, externalState)
		sys.exit(0)
