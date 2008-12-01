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
from pcucontrol  import reboot
from monitor import config
from monitor.database.info.model import FindbadPCURecordSync, FindbadPCURecord, session
from monitor import database
from monitor import util 
from monitor.wrapper import plc, plccache
from nodequery import pcu_select

plc_lock = threading.Lock()
global_round = 1
errorState = {}
count = 0

def nmap_portstatus(status):
	ps = {}
	l_nmap = status.split()
	ports = l_nmap[4:]

	continue_probe = False
	for port in ports:
		results = port.split('/')
		ps[results[0]] = results[1]
		if results[1] == "open":
			continue_probe = True
	return (ps, continue_probe)

def get_pcu(pcuname):
	plc_lock.acquire()
	try:
		#print "GetPCU from PLC %s" % pcuname
		l_pcu  = plc.GetPCUs({'pcu_id' : pcuname})
		#print l_pcu
		if len(l_pcu) > 0:
			l_pcu = l_pcu[0]
	except:
		try:
			#print "GetPCU from file %s" % pcuname
			l_pcus = plccache.l_pcus
			for i in l_pcus:
				if i['pcu_id'] == pcuname:
					l_pcu = i
		except:
			traceback.print_exc()
			l_pcu = None

	plc_lock.release()
	return l_pcu

def get_nodes(node_ids):
	plc_lock.acquire()
	l_node = []
	try:
		l_node = plc.getNodes(node_ids, ['hostname', 'last_contact', 'node_id', 'ports'])
	except:
		try:
			plc_nodes = plccache.l_plcnodes
			for n in plc_nodes:
				if n['node_id'] in node_ids:
					l_node.append(n)
		except:
			traceback.print_exc()
			l_node = None

	plc_lock.release()
	if l_node == []:
		l_node = None
	return l_node
	

def get_plc_pcu_values(pcuname):
	"""
		Try to contact PLC to get the PCU info.
		If that fails, try a backup copy from the last run.
		If that fails, return None
	"""
	values = {}

	l_pcu = get_pcu(pcuname)
	
	if l_pcu is not None:
		site_id = l_pcu['site_id']
		node_ids = l_pcu['node_ids']
		l_node = get_nodes(node_ids) 
				
		if l_node is not None:
			for node in l_node:
				values[node['hostname']] = node['ports'][0]

			values['nodenames'] = [node['hostname'] for node in l_node]

			# NOTE: this is for a dry run later. It doesn't matter which node.
			values['node_id'] = l_node[0]['node_id']

		values.update(l_pcu)
	else:
		values = None
	
	return values

def get_plc_site_values(site_id):
	### GET PLC SITE ######################
	plc_lock.acquire()
	values = {}
	d_site = None

	try:
		d_site = plc.getSites({'site_id': site_id}, ['max_slices', 'slice_ids', 'node_ids', 'login_base'])
		if len(d_site) > 0:
			d_site = d_site[0]
	except:
		try:
			plc_sites = plccache.l_plcsites
			for site in plc_sites:
				if site['site_id'] == site_id:
					d_site = site
					break
		except:
			traceback.print_exc()
			values = None

	plc_lock.release()

	if d_site is not None:
		max_slices = d_site['max_slices']
		num_slices = len(d_site['slice_ids'])
		num_nodes = len(d_site['node_ids'])
		loginbase = d_site['login_base']
		values['plcsite'] = {'num_nodes' : num_nodes, 
							'max_slices' : max_slices, 
							'num_slices' : num_slices,
							'login_base' : loginbase,
							'status'     : 'SUCCESS'}
	else:
		values = None


	return values


def collectPingAndSSH(pcuname, cohash):

	continue_probe = True
	errors = None
	values = {'reboot' : 'novalue'}
	### GET PCU ######################
	try:
		b_except = False
		try:
			v = get_plc_pcu_values(pcuname)
			if v['hostname'] is not None: v['hostname'] = v['hostname'].strip()
			if v['ip'] is not None: v['ip'] = v['ip'].strip()

			if v is not None:
				values['plc_pcu_stats'] = v
			else:
				continue_probe = False
		except:
			b_except = True
			traceback.print_exc()
			continue_probe = False

		if b_except or not continue_probe: return (None, None, None)


		#### COMPLETE ENTRY   #######################

		values['complete_entry'] = []
		#if values['protocol'] is None or values['protocol'] is "":
		#	values['complete_entry'] += ["protocol"]
		if values['plc_pcu_stats']['model'] is None or values['plc_pcu_stats']['model'] is "":
			values['complete_entry'] += ["model"]
			# Cannot continue due to this condition
			continue_probe = False

		if values['plc_pcu_stats']['password'] is None or values['plc_pcu_stats']['password'] is "":
			values['complete_entry'] += ["password"]
			# Cannot continue due to this condition
			continue_probe = False

		if len(values['complete_entry']) > 0:
			continue_probe = False

		if values['plc_pcu_stats']['hostname'] is None or values['plc_pcu_stats']['hostname'] is "":
			values['complete_entry'] += ["hostname"]
		if values['plc_pcu_stats']['ip'] is None or values['plc_pcu_stats']['ip'] is "":
			values['complete_entry'] += ["ip"]

		# If there are no nodes associated with this PCU, then we cannot continue.
		if len(values['plc_pcu_stats']['node_ids']) == 0:
			continue_probe = False
			values['complete_entry'] += ['NoNodeIds']

		#### DNS and IP MATCH #######################
		if values['plc_pcu_stats']['hostname'] is not None and values['plc_pcu_stats']['hostname'] is not "" and \
		   values['plc_pcu_stats']['ip'] is not None and values['plc_pcu_stats']['ip'] is not "":
			#print "Calling socket.gethostbyname(%s)" % values['hostname']
			try:
				ipaddr = socket.gethostbyname(values['plc_pcu_stats']['hostname'])
				if ipaddr == values['plc_pcu_stats']['ip']:
					values['dnsmatch'] = "DNS-OK"
				else:
					values['dnsmatch'] = "DNS-MISMATCH"
					continue_probe = False

			except Exception, err:
				values['dnsmatch'] = "DNS-NOENTRY"
				values['plc_pcu_stats']['hostname'] = values['plc_pcu_stats']['ip']
				#print err
		else:
			if values['plc_pcu_stats']['ip'] is not None and values['plc_pcu_stats']['ip'] is not "":
				values['dnsmatch'] = "NOHOSTNAME"
				values['plc_pcu_stats']['hostname'] = values['plc_pcu_stats']['ip']
			else:
				values['dnsmatch'] = "NO-DNS-OR-IP"
				values['plc_pcu_stats']['hostname'] = "No_entry_in_DB"
				continue_probe = False

		#### RUN NMAP ###############################
		if continue_probe:
			nmap = util.command.CMD()
			(oval,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,23,80,443,5869,9100,16992 %s | grep Host:" % reboot.pcu_name(values['plc_pcu_stats']))
			# NOTE: an empty / error value for oval, will still work.
			(values['portstatus'], continue_probe) = nmap_portstatus(oval)
		else:
			values['portstatus'] = None
			

		######  DRY RUN  ############################
		if 'node_ids' in values['plc_pcu_stats'] and len(values['plc_pcu_stats']['node_ids']) > 0:
			rb_ret = reboot.reboot_test(values['plc_pcu_stats']['nodenames'][0], values, continue_probe, 1, True)
		else:
			rb_ret = "Not_Run" # No nodes to test"

		values['reboot'] = rb_ret

	except:
		print "____________________________________"
		print values
		errors = values
		print "____________________________________"
		errors['traceback'] = traceback.format_exc()
		print errors['traceback']

	values['date_checked'] = time.time()
	return (pcuname, values, errors)

def recordPingAndSSH(request, result):
	global errorState
	global count
	global global_round
	(nodename, values, errors) = result

	if values is not None:
		pcu_id = int(nodename)
		fbsync = FindbadPCURecordSync.findby_or_create(plc_pcuid=0, 
											if_new_set={'round': global_round})
		global_round = fbsync.round
		fbnodesync = FindbadPCURecordSync.findby_or_create(plc_pcuid=pcu_id, 
											if_new_set={'round' : global_round})

		fbrec = FindbadPCURecord(
					date_checked=datetime.fromtimestamp(values['date_checked']),
					round=fbsync.round,
					plc_pcuid=pcu_id,
					plc_pcu_stats=values['plc_pcu_stats'],
					dns_status=values['dnsmatch'],
					port_status=values['portstatus'],
					entry_complete=" ".join(values['complete_entry']),
					reboot_trial_status="%s" % values['reboot'],
				)
		fbnodesync.round = global_round

		fbnodesync.flush()
		fbsync.flush()
		fbrec.flush()

		count += 1
		print "%d %s %s" % (count, nodename, values)

	if errors is not None:
		pcu_id = "id_%s" % nodename
		errorState[pcu_id] = errors
		database.dbDump("findbadpcu_errors", errorState)

# this will be called when an exception occurs within a thread
def handle_exception(request, result):
	print "Exception occured in request %s" % request.requestID
	for i in result:
		print "Result: %s" % i


def checkAndRecordState(l_pcus, cohash):
	global global_round
	global count

	tp = threadpool.ThreadPool(10)

	# CREATE all the work requests
	for pcuname in l_pcus:
		pcu_id = int(pcuname)
		fbnodesync = FindbadPCURecordSync.findby_or_create(plc_pcuid=pcu_id, if_new_set={'round' : 0})
		fbnodesync.flush()

		node_round   = fbnodesync.round
		if node_round < global_round:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(collectPingAndSSH, [pcuname, cohash], {}, 
										 None, recordPingAndSSH, handle_exception)
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

	print FindbadPCURecordSync.query.count()
	print FindbadPCURecord.query.count()
	session.flush()


def main():
	global global_round

	#  monitor.database.if_cached_else_refresh(1, config.refresh, "pculist", lambda : plc.GetPCUs())
	l_pcus = plccache.l_pcus
	cohash = {}

	fbsync = FindbadPCURecordSync.findby_or_create(plc_pcuid=0, if_new_set={'round' : global_round})

	global_round = fbsync.round

	if config.increment:
		# update global round number to force refreshes across all nodes
		global_round += 1
		fbsync.round = global_round

	fbsync.flush()

	if config.site is not None:
		api = plc.getAuthAPI()
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['pcu_ids'])
		pcus = []
		for node in l_nodes:
			pcus += node['pcu_ids']
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]
	elif config.pcuselect is not None:
		n, pcus = pcu_select(config.pcuselect)
		# clear out dups.
		l_pcus = [pcu for pcu in sets.Set(pcus)]

	elif config.nodelist == None and config.pcuid == None:
		print "Calling API GetPCUs() : refresh(%s)" % config.refresh
		l_pcus  = [pcu['pcu_id'] for pcu in l_pcus]
	elif config.nodelist is not None:
		l_pcus = util.file.getListFromFile(config.nodelist)
		l_pcus = [int(pcu) for pcu in l_pcus]
	elif config.pcuid is not None:
		l_pcus = [ config.pcuid ] 
		l_pcus = [int(pcu) for pcu in l_pcus]

	checkAndRecordState(l_pcus, cohash)

	return 0


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
						dbname="findbadpcus", 
						cachenodes=False,
						refresh=False,
						)
	parser.add_option("-f", "--nodelist", dest="nodelist", metavar="FILE", 
						help="Provide the input file for the node list")
	parser.add_option("", "--site", dest="site", metavar="FILE", 
						help="Get all pcus associated with the given site's nodes")
	parser.add_option("", "--pcuselect", dest="pcuselect", metavar="FILE", 
						help="Query string to apply to the findbad pcus")
	parser.add_option("", "--pcuid", dest="pcuid", metavar="id", 
						help="Provide the id for a single pcu")

	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("", "--refresh", action="store_true", dest="refresh",
						help="Refresh the cached values")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)
	try:
		# NOTE: evidently, there is a bizarre interaction between iLO and ssh
		# when LANG is set... Do not know why.  Unsetting LANG, fixes the problem.
		if 'LANG' in os.environ:
			del os.environ['LANG']
		main()
		time.sleep(1)
	except Exception, err:
		traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
