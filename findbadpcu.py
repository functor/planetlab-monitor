#!/usr/bin/python

import os
import sys
import string
import time
import socket
import sets
import signal
import traceback
from datetime import datetime,timedelta
import threadpool
import threading

import monitor
from monitor import config
from monitor.database.info.model import FindbadPCURecord, session
from monitor import database
from monitor import util 
from monitor.wrapper import plc, plccache
from nodequery import pcu_select
from monitor.common import nmap_port_status
from monitor.scanapi import *

plc_lock = threading.Lock()
global_round = 1
errorState = {}
count = 0

# this will be called when an exception occurs within a thread
def handle_exception(request, result):
	print "Exception occured in request %s" % request.requestID
	for i in result:
		print "Result: %s" % i

def checkPCUs(l_pcus, cohash):
	global global_round
	global count

	tp = threadpool.ThreadPool(10)
	scanpcu = ScanPCU(global_round)

	# CREATE all the work requests
	for pcuname in l_pcus:
		pcu_id = int(pcuname)
		#fbnodesync = FindbadPCURecordSync.findby_or_create(plc_pcuid=pcu_id, if_new_set={'round' : 0})
		#fbnodesync.flush()

		#node_round   = fbnodesync.round
		node_round   = global_round - 1
		if node_round < global_round or config.force:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(scanpcu.collectInternal, [int(pcuname), cohash], {}, 
										 None, scanpcu.record, handle_exception)
			tp.putRequest(req)
		else:
			# We just skip it, since it's "up to date"
			count += 1
			print "%d %s %s" % (count, pcu_id, node_round)

	# WAIT while all the work requests are processed.
	begin = time.time()
	while 1:
		try:
			time.sleep(1)
			tp.poll()
			# if more than two hours
			if time.time() - begin > (60*60*1):
				print "findbadpcus.py has run out of time!!!!!!"
				os._exit(1)
		except KeyboardInterrupt:
			print "Interrupted!"
			break
		except threadpool.NoResultsPending:
			print "All results collected."
			break

	#print FindbadPCURecordSync.query.count()
	print FindbadPCURecord.query.count()
	session.flush()


def main():
	global global_round

	l_pcus = plccache.l_pcus
	cohash = {}

	#fbsync = FindbadPCURecordSync.findby_or_create(plc_pcuid=0, 
											#if_new_set={'round' : global_round})

	#global_round = fbsync.round
	api = plc.getAuthAPI()

	if config.site is not None:
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['pcu_ids'])
		pcus = []
		for node in l_nodes:
			pcus += node['pcu_ids']
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]
	elif config.sitelist:
		site_list = config.sitelist.split(',')

		sites = api.GetSites(site_list)
		node_ids = []
		for s in sites:
			node_ids += s['node_ids']

		l_nodes = api.GetNodes(node_ids, ['pcu_ids'])
		pcus = []
		for node in l_nodes:
			pcus += node['pcu_ids']
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]

	elif config.pcuselect is not None:
		n, pcus = pcu_select(config.pcuselect)
		print pcus
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]

	elif config.nodelist == None and config.pcuid == None:
		print "Calling API GetPCUs() : cachecalls(%s)" % config.cachecalls
		l_pcus  = [pcu['pcu_id'] for pcu in l_pcus]
	elif config.nodelist is not None:
		l_pcus = util.file.getListFromFile(config.nodelist)
		l_pcus = [int(pcu) for pcu in l_pcus]
	elif config.pcuid is not None:
		l_pcus = [ config.pcuid ] 
		l_pcus = [int(pcu) for pcu in l_pcus]

	if config.increment:
		# update global round number to force refreshes across all nodes
		global_round += 1

	checkPCUs(l_pcus, cohash)

	if config.increment:
		# update global round number to force refreshes across all nodes
		#fbsync.round = global_round
		#fbsync.flush()
		session.flush()

	return 0


print "main"
if __name__ == '__main__':
	import logging
	logger = logging.getLogger("monitor")
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler("monitor.log", mode = 'a')
	fh.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	from monitor import parser as parsermodule
	parser = parsermodule.getParser()
	parser.set_defaults(nodelist=None, 
						increment=False, 
						pcuid=None,
						pcuselect=None,
						site=None,
						sitelist=None,
						dbname="findbadpcus", 
						cachenodes=False,
						cachecalls=True,
						force=False,
						)
	parser.add_option("-f", "--nodelist", dest="nodelist", metavar="FILE", 
						help="Provide the input file for the node list")
	parser.add_option("", "--site", dest="site", metavar="FILE", 
						help="Get all pcus associated with the given site's nodes")
	parser.add_option("", "--sitelist", dest="sitelist", metavar="FILE", 
						help="Get all pcus associated with the given site's nodes")
	parser.add_option("", "--pcuselect", dest="pcuselect", metavar="FILE", 
						help="Query string to apply to the findbad pcus")
	parser.add_option("", "--pcuid", dest="pcuid", metavar="id", 
						help="Provide the id for a single pcu")

	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("", "--nocachecalls", action="store_false", dest="cachecalls",
						help="Refresh the cached values")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser.add_option("", "--force", action="store_true", dest="force", 
						help="Force probe without incrementing global 'round'.")
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)
	if hasattr(config, 'cachecalls') and not config.cachecalls:
		# NOTE: if explicilty asked, refresh cached values.
		print "Reloading PLCCache"
		plccache.init()
	try:
		# NOTE: evidently, there is a bizarre interaction between iLO and ssh
		# when LANG is set... Do not know why.  Unsetting LANG, fixes the problem.
		if 'LANG' in os.environ:
			del os.environ['LANG']
		main()
		time.sleep(1)
	except Exception, err:
		traceback.print_exc()
		from monitor.common import email_exception
		email_exception()
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
