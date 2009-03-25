#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta
import threadpool
import threading

from monitor.util import file
from pcucontrol.util import command
from monitor import config

from monitor.database.info.model import FindbadNodeRecord, session

from monitor.sources import comon
from monitor.wrapper import plc, plccache
from monitor.scanapi import *

from nodequery import verify,query_to_dict,node_select
import traceback
from monitor.common import nmap_port_status

#print "starting sqlfindbad.py"
# QUERY all nodes.
COMON_COTOPURL= "http://summer.cs.princeton.edu/status/tabulator.cgi?" + \
				"table=table_nodeview&" + \
				"dumpcols='name,resptime,sshstatus,uptime,lastcotop,cpuspeed,memsize,disksize'&" + \
				"formatcsv"
				    #"formatcsv&" + \
					#"select='lastcotop!=0'"

api = plc.getAuthAPI()
plc_lock = threading.Lock()
round = 1
global_round = round
count = 0

# this will be called when an exception occurs within a thread
def handle_exception(request, result):
	print "Exception occured in request %s" % request.requestID
	for i in result:
		print "Result: %s" % i
		

def checkAndRecordState(l_nodes, cohash):
	global global_round
	global count

	tp = threadpool.ThreadPool(20)
	scannode = ScanNodeInternal(global_round)

	# CREATE all the work requests
	for nodename in l_nodes:
		#fbnodesync = FindbadNodeRecordSync.findby_or_create(hostname=nodename, if_new_set={'round':0})
		#node_round   = fbnodesync.round
		node_round = global_round - 1
		#fbnodesync.flush()

		if node_round < global_round or config.force:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(scannode.collectInternal, [nodename, cohash], {}, 
										 None, scannode.record, handle_exception)
			tp.putRequest(req)
		else:
			# We just skip it, since it's "up to date"
			count += 1
			#print "%d %s %s" % (count, nodename, externalState['nodes'][nodename]['values'])
			print "%d %s %s" % (count, nodename, node_round)

	# WAIT while all the work requests are processed.
	begin = time.time()
	while 1:
		try:
			time.sleep(1)
			tp.poll()
			# if more than two hours
			if time.time() - begin > (60*60*1.5):
				print "findbad.py has run out of time!!!!!!"
				os._exit(1)
		except KeyboardInterrupt:
			print "Interrupted!"
			break
		except threadpool.NoResultsPending:
			print "All results collected."
			break

	#print FindbadNodeRecordSync.query.count()
	print FindbadNodeRecord.query.count()
	session.flush()

def main():
	global global_round

	#fbsync = FindbadNodeRecordSync.findby_or_create(hostname="global", 
	#												if_new_set={'round' : global_round})
	#global_round = fbsync.round

	if config.increment:
		# update global round number to force refreshes across all nodes
		global_round += 1

	cotop = comon.Comon()
	# lastcotop measures whether cotop is actually running.  this is a better
	# metric than sshstatus, or other values from CoMon
	cotop_url = COMON_COTOPURL

	# history information for all nodes
	cohash = {}
	#cohash = cotop.coget(cotop_url)
	l_nodes = plccache.l_nodes
	if config.nodelist:
		f_nodes = file.getListFromFile(config.nodelist)
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.node:
		f_nodes = [config.node]
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.nodegroup:
		ng = api.GetNodeGroups({'name' : config.nodegroup})
		l_nodes = api.GetNodes(ng[0]['node_ids'])
	elif config.site:
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['hostname'])
	elif config.sitelist:
		site_list = config.sitelist.split(',')
		sites = api.GetSites(site_list)
		node_ids = []
		for s in sites:
			node_ids += s['node_ids']
		l_nodes = api.GetNodes(node_ids, ['hostname'])
		
	l_nodes = [node['hostname'] for node in l_nodes]

	# perform this query after the above options, so that the filter above
	# does not break.
	if config.nodeselect:
		plcnodes = api.GetNodes({'peer_id' : None}, ['hostname'])
		plcnodes = [ node['hostname'] for node in plcnodes ]
		l_nodes = node_select(config.nodeselect, plcnodes, None)

	print "fetching %s hosts" % len(l_nodes)

	checkAndRecordState(l_nodes, cohash)

	if config.increment:
		# update global round number to force refreshes across all nodes
		#fbsync.round = global_round
		#fbsync.flush()
		pass

	return 0


if __name__ == '__main__':
	from monitor import parser as parsermodule

	parser = parsermodule.getParser(['nodesets'])

	parser.set_defaults( increment=False, dbname="findbad", cachenodes=False, 
						force=False,)
	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser.add_option("", "--force", action="store_true", dest="force", 
						help="Force probe without incrementing global 'round'.")

	parser = parsermodule.getParser(['defaults'], parser)
	
	cfg = parsermodule.parse_args(parser)

	try:
		main()
	except Exception, err:
		print traceback.print_exc()
		from monitor.common import email_exception
		email_exception()
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
	print "sleeping"
