#!/usr/bin/python

import os
import sys
import string
import time
import socket

    
import signal
import traceback

#old_handler = signal.getsignal(signal.SIGCHLD)

#def sig_handler(signum, stack):
#	""" Handle SIGCHLD signal """
#	global old_handler
#	if signum == signal.SIGCHLD:
#		try:
#			os.wait()
#		except:
#			pass
#	if old_handler != signal.SIG_DFL:
#		old_handler(signum, stack)
#
#orig_sig_handler = signal.signal(signal.SIGCHLD, sig_handler)


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
externalState = {'round': round, 'nodes': {'a': None}}
errorState = {}
count = 0

import reboot
from reboot import pcu_name

import database
import moncommands
import plc
import comon
import threadpool
import syncplcdb

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
		print "GetPCU from PLC %s" % pcuname
		l_pcu  = plc.GetPCUs({'pcu_id' : pcuname})
		print l_pcu
		if len(l_pcu) > 0:
			l_pcu = l_pcu[0]
	except:
		try:
			print "GetPCU from file %s" % pcuname
			l_pcus = database.dbLoad("pculist")
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
			plc_nodes = database.dbLoad("l_plcnodes")
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
			plc_sites = database.dbLoad("l_plcsites")
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
	values = {}
	### GET PCU ######################
	try:
		b_except = False
		try:
			v = get_plc_pcu_values(pcuname)
			if v is not None:
				values.update(v)
			else:
				continue_probe = False
		except:
			b_except = True
			traceback.print_exc()
			continue_probe = False

		if b_except or not continue_probe: return (None, None, None)

		if values['hostname'] is not None:
			values['hostname'] = values['hostname'].strip()

		if values['ip'] is not None:
			values['ip'] = values['ip'].strip()

		#### COMPLETE ENTRY   #######################

		values['complete_entry'] = []
		#if values['protocol'] is None or values['protocol'] is "":
		#	values['complete_entry'] += ["protocol"]
		if values['model'] is None or values['model'] is "":
			values['complete_entry'] += ["model"]
			# Cannot continue due to this condition
			continue_probe = False

		if values['password'] is None or values['password'] is "":
			values['complete_entry'] += ["password"]
			# Cannot continue due to this condition
			continue_probe = False

		if len(values['complete_entry']) > 0:
			continue_probe = False

		if values['hostname'] is None or values['hostname'] is "":
			values['complete_entry'] += ["hostname"]
		if values['ip'] is None or values['ip'] is "":
			values['complete_entry'] += ["ip"]

		# If there are no nodes associated with this PCU, then we cannot continue.
		if len(values['node_ids']) == 0:
			continue_probe = False
			values['complete_entry'] += ['NoNodeIds']

		#### DNS and IP MATCH #######################
		if values['hostname'] is not None and values['hostname'] is not "" and \
		   values['ip'] is not None and values['ip'] is not "":
			#print "Calling socket.gethostbyname(%s)" % values['hostname']
			try:
				ipaddr = socket.gethostbyname(values['hostname'])
				if ipaddr == values['ip']:
					values['dnsmatch'] = "DNS-OK"
				else:
					values['dnsmatch'] = "DNS-MISMATCH"
					continue_probe = False

			except Exception, err:
				values['dnsmatch'] = "DNS-NOENTRY"
				values['hostname'] = values['ip']
				#print err
		else:
			if values['ip'] is not None and values['ip'] is not "":
				values['dnsmatch'] = "NOHOSTNAME"
				values['hostname'] = values['ip']
			else:
				values['dnsmatch'] = "NO-DNS-OR-IP"
				values['hostname'] = "No_entry_in_DB"
				continue_probe = False

		#### RUN NMAP ###############################
		if continue_probe:
			nmap = moncommands.CMD()
			(oval,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,23,80,443,5869,9100,16992 %s | grep Host:" % pcu_name(values))
			# NOTE: an empty / error value for oval, will still work.
			(values['portstatus'], continue_probe) = nmap_portstatus(oval)
		else:
			values['portstatus'] = None
			

		######  DRY RUN  ############################
		if 'node_ids' in values and len(values['node_ids']) > 0:
			rb_ret = reboot.reboot_test(values['nodenames'][0], values, continue_probe, 1, True)
		else:
			rb_ret = "Not_Run" # No nodes to test"

		values['reboot'] = rb_ret

		### GET PLC SITE ######################
		v = get_plc_site_values(values['site_id'])
		if v is not None:
			values.update(v)
		else:
			values['plcsite'] = {'status' : "GS_FAILED"}
			
	except:
		print "____________________________________"
		print values
		errors = values
		print "____________________________________"
		errors['traceback'] = traceback.format_exc()
		print errors['traceback']

	values['checked'] = time.time()
	return (pcuname, values, errors)

def recordPingAndSSH(request, result):
	global errorState
	global externalState
	global count
	(nodename, values, errors) = result

	if values is not None:
		global_round = externalState['round']
		pcu_id = "id_%s" % nodename
		externalState['nodes'][pcu_id]['values'] = values
		externalState['nodes'][pcu_id]['round'] = global_round

		count += 1
		print "%d %s %s" % (count, nodename, externalState['nodes'][pcu_id]['values'])
		database.dbDump(config.dbname, externalState)

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
	global externalState
	global count
	global_round = externalState['round']

	tp = threadpool.ThreadPool(20)

	# CREATE all the work requests
	for pcuname in l_pcus:
		pcu_id = "id_%s" % pcuname
		if pcuname not in externalState['nodes']:
			#print type(externalState['nodes'])

			externalState['nodes'][pcu_id] = {'round': 0, 'values': []}

		node_round   = externalState['nodes'][pcu_id]['round']
		if node_round < global_round:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(collectPingAndSSH, [pcuname, cohash], {}, 
										 None, recordPingAndSSH, handle_exception)
			tp.putRequest(req)
		else:
			# We just skip it, since it's "up to date"
			count += 1
			print "%d %s %s" % (count, pcu_id, externalState['nodes'][pcu_id]['values'])
			pass

	# WAIT while all the work requests are processed.
	begin = time.time()
	while 1:
		try:
			time.sleep(1)
			tp.poll()
			# if more than two hours
			if time.time() - begin > (60*60*1):
				print "findbadpcus.py has run out of time!!!!!!"
				database.dbDump(config.dbname, externalState)
				os._exit(1)
		except KeyboardInterrupt:
			print "Interrupted!"
			break
		except threadpool.NoResultsPending:
			print "All results collected."
			break



def main():
	global externalState

	l_pcus = database.if_cached_else_refresh(1, config.refresh, "pculist", lambda : plc.GetPCUs())
	externalState = database.if_cached_else(1, config.dbname, lambda : externalState) 
	cohash = {}

	if config.increment:
		# update global round number to force refreshes across all nodes
		externalState['round'] += 1

	if config.nodelist == None and config.pcuid == None:
		print "Calling API GetPCUs() : refresh(%s)" % config.refresh
		l_pcus  = [pcu['pcu_id'] for pcu in l_pcus]
	elif config.nodelist is not None:
		l_pcus = config.getListFromFile(config.nodelist)
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
	import parser as parsermodule
	parser = parsermodule.getParser()
	parser.set_defaults(nodelist=None, 
						increment=False, 
						pcuid=None,
						dbname="findbadpcus", 
						cachenodes=False,
						refresh=False,
						)
	parser.add_option("-f", "--nodelist", dest="nodelist", metavar="FILE", 
						help="Provide the input file for the node list")
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
		database.dbDump(config.dbname, externalState)
		sys.exit(0)
