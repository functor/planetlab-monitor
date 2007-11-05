#!/usr/bin/python

import os
import sys
import string
import time
import socket

    
import signal

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

from config import config
from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(filename="", 
					increment=False, 
					dbname="findbadpcus", 
					cachenodes=False,
					refresh=False,
					)
parser.add_option("-f", "--nodelist", dest="filename", metavar="FILE", 
					help="Provide the input file for the node list")
parser.add_option("", "--cachenodes", action="store_true",
					help="Cache node lookup from PLC")
parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
					help="Specify the name of the database to which the information is saved")
parser.add_option("", "--refresh", action="store_true", dest="refresh",
					help="Refresh the cached values")
parser.add_option("-i", "--increment", action="store_true", dest="increment", 
					help="Increment round number to force refresh or retry")
config = config(parser)
config.parse_args()

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
count = 0

import reboot
from reboot import pcu_name

import soltesz
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

def collectPingAndSSH(pcuname, cohash):

	continue_probe = True
	values = {}
	### GET PCU ######################
	try:
		b_except = False
		plc_lock.acquire()

		try:
			l_pcu  = plc.GetPCUs({'pcu_id' : pcuname})
			
			if len(l_pcu) > 0:
				node_ids = l_pcu[0]['node_ids']
				l_node = plc.getNodes(node_ids, ['hostname', 'last_contact', 'node_id'])
				site_id = l_pcu[0]['site_id']

				values['pcu_id'] = l_pcu[0]['pcu_id']

			if len(l_node) > 0:
				values['nodenames'] = [node['hostname'] for node in l_node]
				# NOTE: this is for a dry run later. It doesn't matter which node.
				values['node_id'] = l_node[0]['node_id']

			if len(l_pcu) > 0:
				values.update(l_pcu[0])
			else:
				continue_probe = False

		except:
			b_except = True
			import traceback
			traceback.print_exc()

			continue_probe = False

		plc_lock.release()
		if b_except: return (None, None)

		if values['hostname'] is not None:
			values['hostname'] = values['hostname'].strip()

		if values['ip'] is not None:
			values['ip'] = values['ip'].strip()

		#### COMPLETE ENTRY   #######################

		values['complete_entry'] = []
		if values['protocol'] is None or values['protocol'] is "":
			values['complete_entry'] += ["protocol"]
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
			nmap = soltesz.CMD()
			(oval,eval) = nmap.run_noexcept("nmap -oG - -p22,23,80,443,16992 %s | grep Host:" % pcu_name(values))
			# NOTE: an empty / error value for oval, will still work.
			(values['portstatus'], continue_probe) = nmap_portstatus(oval)

		######  DRY RUN  ############################
		node_ids = values['node_ids']
		ports = values['ports']
		nid2port = {}
		i = 0

		for id in node_ids:
			nid2port[id] = ports[i]
			i += 1

		# ####
		# TODO: check port status above for whether or not to try...
		# ####
		# DataProbe iPal (many sites)
		if  continue_probe and values['model'].find("Dataprobe IP-41x/IP-81x") >= 0:
			if values['portstatus']['23'] == "open":
				rb_ret = reboot.ipal_reboot(pcu_name(values),
										values['password'],
										nid2port[values['node_id']],
										True)
			else:
				rb_ret = "Unsupported_Port"
				

		# APC Masterswitch (Berkeley)
		elif continue_probe and values['model'].find("APC AP79xx/Masterswitch") >= 0:
			if  values['portstatus']['22'] == "open" or \
				values['portstatus']['23'] == "open":
				rb_ret = reboot.apc_reboot(pcu_name(values),
										values['username'],
										values['password'], 
										nid2port[values['node_id']], 
										values['portstatus'], 
										True)
			else:
				rb_ret = "Unsupported_Port"
		# BayTech DS4-RPC
		elif continue_probe and values['model'].find("Baytech DS4-RPC") >= 0:
			if values['portstatus']['22'] == "open":
				rb_ret = reboot.baytech_reboot(pcu_name(values),
										   values['username'],
										   values['password'], 
										   nid2port[values['node_id']], 
										   True)
			else:
				rb_ret = "Unsupported_Port"
				

		# iLO
		elif continue_probe and values['model'].find("HP iLO") >= 0:
			if values['portstatus']['22'] == "open":
				rb_ret = reboot.ilo_reboot(pcu_name(values),
										   values['username'],
										   values['password'], 
										   True)
			else:
				rb_ret = "Unsupported_Port"
				
		# DRAC ssh
		elif continue_probe and values['model'].find("Dell RAC") >= 0:
			if values['portstatus']['22'] == "open":
				rb_ret = reboot.drac_reboot(pcu_name(values),
										   values['username'],
										   values['password'], 
										   True)
			else:
				rb_ret = "Unsupported_Port"
				

		# BlackBox PSExxx-xx (e.g. PSE505-FR)
		elif continue_probe and \
			(values['model'].find("BlackBox PS5xx") >= 0 or
			 values['model'].find("ePowerSwitch 1/4/8x") >=0 ):
			if values['portstatus']['80'] == "open":
				rb_ret = reboot.bbpse_reboot(pcu_name(values),
								values['username'], 
								values['password'], 
								nid2port[values['node_id']], 
								80,
								True)
			else:
				rb_ret = "Unsupported_PCU"
				
		# x10toggle
		elif 	continue_probe and values['protocol'] == "ssh" and \
				values['model'] == "x10toggle":
			rb_ret = reboot.x10toggle_reboot(pcu_name(values),
											values['username'],
											values['password'], 
											nid2port[values['node_id']], 
											True)
		# ????
		elif continue_probe and values['protocol'] == "racadm" and \
				values['model'] == "RAC":
			rb_ret = reboot.racadm_reboot(pcu_name(values),
										  values['username'],
										  values['password'],
										  nid2port[values['node_id']], 
										  True)
		elif continue_probe:
			rb_ret = "Unsupported_PCU"

		elif continue_probe == False:
			if 'portstatus' in values:
				rb_ret = "NetDown"
			else:
				rb_ret = "Not_Run"
		else:
			rb_ret = -1

		values['reboot'] = rb_ret

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
	except:
		print "____________________________________"
		print values
		print "____________________________________"
		import traceback
		traceback.print_exc()

	return (pcuname, values)

def recordPingAndSSH(request, result):
	global externalState
	global count
	(nodename, values) = result

	if values is not None:
		global_round = externalState['round']
		pcu_id = "id_%s" % nodename
		externalState['nodes'][pcu_id]['values'] = values
		externalState['nodes'][pcu_id]['round'] = global_round

		count += 1
		print "%d %s %s" % (count, nodename, externalState['nodes'][pcu_id]['values'])
		soltesz.dbDump(config.dbname, externalState)

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
	cohash = {}

	if config.increment:
		# update global round number to force refreshes across all nodes
		externalState['round'] += 1

	if config.filename == "":
		print "Calling API GetPCUs() : refresh(%s)" % config.refresh
		l_pcus = soltesz.if_cached_else_refresh(1, 
								config.refresh, "pculist", lambda : plc.GetPCUs())
		l_pcus  = [pcu['pcu_id'] for pcu in l_pcus]
	else:
		l_pcus = config.getListFromFile(config.filename)
		l_pcus = [int(pcu) for pcu in l_pcus]

	checkAndRecordState(l_pcus, cohash)

	return 0

import logging
logger = logging.getLogger("monitor")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("monitor.log", mode = 'a')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


if __name__ == '__main__':
	try:
		# NOTE: evidently, there is a bizarre interaction between iLO and ssh
		# when LANG is set... Do not know why.  Unsetting LANG, fixes the problem.
		if 'LANG' in os.environ:
			del os.environ['LANG']
		main()
		time.sleep(1)
	except Exception, err:
		print "Exception: %s" % err
		print "Saving data... exitting."
		soltesz.dbDump(config.dbname, externalState)
		sys.exit(0)
