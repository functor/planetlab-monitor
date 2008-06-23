#!/usr/bin/python

import os
import sys
import string
import time


# QUERY all nodes.
COMON_COTOPURL= "http://summer.cs.princeton.edu/status/tabulator.cgi?" + \
					"table=table_nodeview&" + \
				    "dumpcols='name,resptime,sshstatus,uptime,lastcotop'&" + \
				    "formatcsv"
				    #"formatcsv&" + \
					#"select='lastcotop!=0'"

import threading
plc_lock = threading.Lock()
round = 1
externalState = {'round': round, 'nodes': {}}
count = 0


import soltesz
import comon
import threadpool
import syncplcdb

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

def collectPingAndSSH(nodename, cohash):
	### RUN PING ######################
	ping = soltesz.CMD()
	(oval,eval) = ping.run_noexcept("ping -c 1 -q %s | grep rtt" % nodename)

	values = {}

	if oval == "":
		# An error occurred
		values['ping'] = "NOPING"
	else:
		values['ping'] = "PING"

	#uptime = soltesz.SSH('root', nodename)
	#(oval,eval) = uptime.run_noexcept("uptime | awk '{print $3,$4}' | tr , ' '")

	### RUN SSH ######################
	b_getbootcd_id = True
	ssh = soltesz.SSH('root', nodename)
	oval = ""
	eval = ""
	(oval, eval) = ssh.run_noexcept('echo `uname -a ; ls /tmp/bm.log`')
	val = oval
	if "2.6.17" in oval or "2.6.2" in oval:
		values['ssh'] = 'SSH'
		values['category'] = 'ALPHA'
		if "bm.log" in oval:
			values['state'] = 'DEBUG'
		else:
			values['state'] = 'BOOT'
	elif "2.6.12" in oval or "2.6.10" in oval:
		values['ssh'] = 'SSH'
		values['category'] = 'PROD'
		if "bm.log" in oval:
			values['state'] = 'DEBUG'
		else:
			values['state'] = 'BOOT'
	elif "2.4" in oval:
		b_getbootcd_id = False
		values['ssh'] = 'SSH'
		values['category'] = 'OLDBOOTCD'
		values['state'] = 'DEBUG'
	elif oval != "":
		values['ssh'] = 'SSH'
		values['category'] = 'UNKNOWN'
		if "bm.log" in oval:
			values['state'] = 'DEBUG'
		else:
			values['state'] = 'BOOT'
	else:
		# An error occurred.
		b_getbootcd_id = False
		values['ssh'] = 'NOSSH'
		values['category'] = 'ERROR'
		values['state'] = 'DOWN'
		val = eval.strip()

	values['kernel'] = val

	if b_getbootcd_id:
		# try to get BootCD for all nodes that are not 2.4 nor inaccessible
		(oval, eval) = ssh.run_noexcept('cat /mnt/cdrom/bootme/ID')
		val = oval
		if "BootCD" in val:
			values['bootcd'] = val
			if "v2" in val and \
				( nodename is not "planetlab1.cs.unc.edu" and \
				  nodename is not "planetlab2.cs.unc.edu" ):
				values['category'] = 'OLDBOOTCD'
		else:
			values['bootcd'] = ""
	else:
		values['bootcd'] = ""

	# TODO: get bm.log for debug nodes.
	# 'zcat /tmp/bm.log'
		
	if nodename in cohash: 
		values['comonstats'] = cohash[nodename]
	else:
		values['comonstats'] = {'resptime':  '-1', 
								'uptime':    '-1',
								'sshstatus': '-1', 
								'lastcotop': '-1'}
	# include output value
	### GET PLC NODE ######################
	b_except = False
	plc_lock.acquire()

	try:
		d_node = plc.getNodes({'hostname': nodename}, ['pcu_ids', 'site_id', 'last_contact', 'boot_state', 'nodegroup_ids'])
	except:
		b_except = True
		import traceback
		b_except = True
		import traceback
		traceback.print_exc()

	plc_lock.release()
	if b_except: return (None, None)

	site_id = -1
	if d_node and len(d_node) > 0:
		pcu = d_node[0]['pcu_ids']
		if len(pcu) > 0:
			values['pcu'] = "PCU"
		else:
			values['pcu'] = "NOPCU"
		site_id = d_node[0]['site_id']
		last_contact = d_node[0]['last_contact']
		nodegroups = d_node[0]['nodegroup_ids']
		values['plcnode'] = {'status' : 'SUCCESS', 
							'pcu_ids': pcu, 
							'boot_state' : d_node[0]['boot_state'],
							'site_id': site_id,
							'nodegroups' : nodegroups,
							'last_contact': last_contact}
	else:
		values['pcu']     = "UNKNOWN"
		values['plcnode'] = {'status' : "GN_FAILED"}
		

	### GET PLC SITE ######################
	b_except = False
	plc_lock.acquire()

	try:
		d_site = plc.getSites({'site_id': site_id}, 
							['max_slices', 'slice_ids', 'node_ids', 'login_base'])
	except:
		b_except = True
		import traceback
		traceback.print_exc()

	plc_lock.release()
	if b_except: return (None, None)

	if d_site and len(d_site) > 0:
		max_slices = d_site[0]['max_slices']
		num_slices = len(d_site[0]['slice_ids'])
		num_nodes = len(d_site[0]['node_ids'])
		loginbase = d_site[0]['login_base']
		values['plcsite'] = {'num_nodes' : num_nodes, 
							'max_slices' : max_slices, 
							'num_slices' : num_slices,
							'login_base' : loginbase,
							'status'     : 'SUCCESS'}
	else:
		values['plcsite'] = {'status' : "GS_FAILED"}

	values['checked'] = time.time()

	return (nodename, values)

def recordPingAndSSH(request, result):
	global externalState
	global count
	(nodename, values) = result

	if values is not None:
		global_round = externalState['round']
		externalState['nodes'][nodename]['values'] = values
		externalState['nodes'][nodename]['round'] = global_round

		count += 1
		print "%d %s %s" % (count, nodename, externalState['nodes'][nodename]['values'])
		soltesz.dbDump(config.dbname, externalState)

# this will be called when an exception occurs within a thread
def handle_exception(request, result):
	print "Exception occured in request %s" % request.requestID
	for i in result:
		print "Result: %s" % i


def checkAndRecordState(l_nodes, cohash):
	global externalState
	global count
	global_round = externalState['round']

	tp = threadpool.ThreadPool(20)

	# CREATE all the work requests
	for nodename in l_nodes:
		if nodename not in externalState['nodes']:
			externalState['nodes'][nodename] = {'round': 0, 'values': []}

		node_round   = externalState['nodes'][nodename]['round']
		if node_round < global_round:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(collectPingAndSSH, [nodename, cohash], {}, 
										 None, recordPingAndSSH, handle_exception)
			tp.putRequest(req)
		else:
			# We just skip it, since it's "up to date"
			count += 1
			print "%d %s %s" % (count, nodename, externalState['nodes'][nodename]['values'])
			pass

	# WAIT while all the work requests are processed.
	while 1:
		try:
			time.sleep(1)
			tp.poll()
		except KeyboardInterrupt:
			print "Interrupted!"
			break
		except threadpool.NoResultsPending:
			print "All results collected."
			break



def main():
	global externalState

	externalState = soltesz.if_cached_else(1, config.dbname, lambda : externalState) 

	if config.increment:
		# update global round number to force refreshes across all nodes
		externalState['round'] += 1

	cotop = comon.Comon()
	# lastcotop measures whether cotop is actually running.  this is a better
	# metric than sshstatus, or other values from CoMon
	cotop_url = COMON_COTOPURL

	# history information for all nodes
	cohash = cotop.coget(cotop_url)
	l_nodes = syncplcdb.create_plcdb()
	if config.filename:
		f_nodes = config.getListFromFile(config.filename)
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.node:
		f_nodes = [config.node]
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.nodegroup:
		ng = api.GetNodeGroups({'name' : config.nodegroup})
		l_nodes = api.GetNodes(ng[0]['node_ids'])

	l_nodes = [node['hostname'] for node in l_nodes]

	print "fetching %s hosts" % len(l_nodes)

	checkAndRecordState(l_nodes, cohash)

	return 0


if __name__ == '__main__':
	from config import config
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(filename=None, node=None, nodegroup=None, increment=False, dbname="findbadnodes", cachenodes=False)
	parser.add_option("", "--node", dest="node", metavar="hostname", 
						help="Provide a single node to operate on")
	parser.add_option("-f", "--nodelist", dest="filename", metavar="FILE", 
						help="Provide the input file for the node list")
	parser.add_option("", "--nodegroup", dest="nodegroup", metavar="FILE", 
						help="Provide the nodegroup for the list of nodes.")

	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	config = config(parser)
	config.parse_args()

	try:
		main()
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		soltesz.dbDump(config.dbname, externalState)
		sys.exit(0)
