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

import plc
api = plc.getAuthAPI()
from unified_model import *
from const import MINUP

round = 1
externalState = {'round': round, 'nodes': {}}
count = 0

def main(config):
	global externalState
	externalState = database.if_cached_else(1, config.dbname, lambda : externalState) 
	if config.increment:
		# update global round number to force refreshes across all nodes
		externalState['round'] += 1

	l_nodes = syncplcdb.create_plcdb()
	l_plcnodes = database.dbLoad("l_plcnodes")

	l_nodes = get_nodeset(config)
	print len(l_nodes)
	#if config.node:
	#	l_nodes = [config.node]
	##else:
	#	l_nodes = [node['hostname'] for node in l_plcnodes]
	
	checkAndRecordState(l_nodes, l_plcnodes)

def checkAndRecordState(l_nodes, l_plcnodes):
	global externalState
	global count
	global_round = externalState['round']

	for nodename in l_nodes:
		if nodename not in externalState['nodes']:
			externalState['nodes'][nodename] = {'round': 0, 'values': []}

		node_round   = externalState['nodes'][nodename]['round']
		if node_round < global_round:
			# do work
			values = collectStatusAndState(nodename, l_plcnodes)
			global_round = externalState['round']
			externalState['nodes'][nodename]['values'] = values
			externalState['nodes'][nodename]['round'] = global_round
		else:
			pf = PersistFlags(nodename, 1, db='node_persistflags')
			print "%d %35s %s since %s" % (count, nodename, pf.status, pf.last_changed)
			del pf
			count += 1

		if count % 20 == 0:
			database.dbDump(config.dbname, externalState)

	database.dbDump(config.dbname, externalState)

fb = database.dbLoad('findbad')

def getnodesup(nodelist):
	up = 0
	for node in nodelist:
		if node['hostname'] in fb['nodes'].keys():
			try:
				if fb['nodes'][node['hostname']]['values']['state'] == "BOOT":
					up = up + 1
			except:
				pass
	return up

def get(fb, path):
	indexes = path.split("/")
	values = fb
	for index in indexes:
		if index in values:
			values = values[index]
		else:
			return None
	return values

def collectStatusAndState(nodename, l_plcnodes):
	global count

	d_node = None
	for node in l_plcnodes:
		if node['hostname'] == nodename:
			d_node = node
			break
	if not d_node:
		return None

	pf = PersistFlags(nodename, 1, db='node_persistflags')

	if not pf.checkattr('last_changed'):
		pf.last_changed = time.time()
		
	pf.last_checked = time.time()

	if not pf.checkattr('status'):
		pf.status = "unknown"

	state_path     = "nodes/" + nodename + "/values/state"
	bootstate_path = "nodes/" + nodename + "/values/plcnode/boot_state"

	if get(fb, state_path) == "BOOT":
		if pf.status != "good": pf.last_changed = time.time()
		pf.status = "good"
	elif get(fb, state_path)  == "DEBUG":
		bs = get(fb, bootstate_path)
		if pf.status != bs: pf.last_changed = time.time()
		pf.status = bs
	else:
		if pf.status != "down": pf.last_changed = time.time()
		pf.status = "down"

	count += 1
	print "%d %35s %s since(%s)" % (count, nodename, pf.status, diff_time(pf.last_changed))
	# updated by other modules
	#pf.enabled = 
	#pf.suspended = 

	pf.save()

	return True

if __name__ == '__main__':
	import parser as parsermodule
	parser = parsermodule.getParser(['nodesets'])
	parser.set_defaults(filename=None, node=None, nodeselect=False, nodegroup=None, 
						increment=False, dbname="nodebad", cachenodes=False)
	
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)

	try:
		main(config)
	except Exception, err:
		import traceback
		print traceback.print_exc()
		from nodecommon import email_exception
		email_exception()
		print "Exception: %s" % err
		print "Saving data... exitting."
		database.dbDump(config.dbname, externalState)
		sys.exit(0)
