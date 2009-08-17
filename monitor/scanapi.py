#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta
import threadpool
import threading

import socket
from pcucontrol import reboot

from pcucontrol.util import command
from monitor import config

from monitor.database.info.model import *

from monitor.sources import comon
from monitor.wrapper import plc, plccache

import traceback
from monitor.common import nmap_port_status, email_exception

COMON_COTOPURL= "http://summer.cs.princeton.edu/status/tabulator.cgi?" + \
			"table=table_nodeview&" + \
			"dumpcols='name,resptime,sshstatus,uptime,lastcotop,cpuspeed,memsize,disksize'&" + \
			"formatcsv"

api = plc.getAuthAPI()
plc_lock = threading.Lock()
round = 1
global_round = round
count = 0


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
			plc_nodes = plccache.l_nodes
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

class ScanInterface(object):
	recordclass = None
	syncclass = None
	primarykey = 'hostname'

	def __init__(self, round=1):
		self.round = round
		self.count = 1

	def __getattr__(self, name):
		if 'collect' in name or 'record' in name:
			method = getattr(self, name, None)
			if method is None:
				raise Exception("No such method %s" % name)
			return method
		else:
			raise Exception("No such method %s" % name)

	def collect(self, nodename, data):
		pass

	def record(self, request, (nodename, values) ):

		try:
			if values is None:
				return
			
			if self.syncclass:
				fbnodesync = self.syncclass.findby_or_create(
												#if_new_set={'round' : self.round},
												**{ self.primarykey : nodename})
			# NOTE: This code will either add a new record for the new self.round, 
			# 	OR it will find the previous value, and update it with new information.
			#	The data that is 'lost' is not that important, b/c older
			#	history still exists.  
			fbrec = self.recordclass.findby_or_create(
						**{ self.primarykey:nodename})

			fbrec.set( **values ) 

			fbrec.flush()
			if self.syncclass:
				fbnodesync.round = self.round
				fbnodesync.flush()

			print "%d %s %s" % (self.count, nodename, values)
			self.count += 1

		except:
			print "ERROR:"
			email_exception(str(nodename))
			print traceback.print_exc()
			pass

class ScanNodeInternal(ScanInterface):
	recordclass = FindbadNodeRecord
	#syncclass = FindbadNodeRecordSync
	syncclass = None
	primarykey = 'hostname'

	def collectPorts(self, nodename, port_list=[22,80,806]):
		values = {}
		for port in port_list:
			ret = os.system("nc -w 5 -z %s %s > /dev/null" % (nodename, port) )
			if ret == 0:
				values[str(port)] = "open"
			else:
				values[str(port)] = "closed"
		return {'port_status' : values }

	def collectNMAP(self, nodename, cohash):
		#### RUN NMAP ###############################
		# NOTE: run the same command three times and take the best of three
		# 		runs.  NMAP can drop packets, and especially so when it runs many
		# 		commands at once.
		values = {}
		nmap = command.CMD()
		print "nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename
		(oval1,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename)
		(oval2,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename)
		(oval3,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename)
		# NOTE: an empty / error value for oval, will still work.
		values['port_status'] = {}
		(o1,continue_probe) = nmap_port_status(oval1)
		(o2,continue_probe) = nmap_port_status(oval2)
		(o3,continue_probe) = nmap_port_status(oval3)
		for p in ['22', '80', '806']:
			l = [ o1[p], o2[p], o3[p] ]
			if len(filter(lambda x: x == 'open', l)) > 1:
				values['port_status'][p] = 'open'
			else:
				values['port_status'][p] = o1[p]

		print values['port_status']
		return (nodename, values)

	def collectPING(self, nodename, cohash):
		values = {}
		ping = command.CMD()
		(oval,errval) = ping.run_noexcept("ping -c 1 -q %s | grep rtt" % nodename)

		values = {}
		if oval == "":
			# An error occurred
			values['ping_status'] = False
		else:
			values['ping_status'] = True

		return values

	def collectTRACEROUTE(self, nodename, cohash):
		values = {}
		trace = command.CMD()
		(oval,errval) = trace.run_noexcept("traceroute %s" % nodename)

		values['traceroute'] = oval

		return values

	def collectSSH(self, nodename, cohash):
		values = {}
		try:
			for port in [22, 806]: 
				ssh = command.SSH('root', nodename, port)

				(oval, errval) = ssh.run_noexcept2(""" <<\EOF
					echo "{"
					echo '  "kernel_version":"'`uname -a`'",'
					echo '  "bmlog":"'`ls /tmp/bm.log`'",'
					echo '  "bootcd_version":"'`cat /mnt/cdrom/bootme/ID`'",'
					echo '  "nm_status":"'`ps ax | grep nm.py | grep -v grep`'",'
					echo '  "dns_status":"'`host boot.planet-lab.org 2>&1`'",'
					echo '  "princeton_comon_dir":"'`ls -d /vservers/princeton_comon`'",'
					echo '  "uptime":"'`cat /proc/uptime`'",'

					ID=`grep princeton_comon /etc/passwd | awk -F : '{if ( $3 > 500 ) { print $3}}'` 
					echo '  "princeton_comon_running":"'`ls -d /proc/virtual/$ID`'",'
					echo '  "princeton_comon_procs":"'`vps ax | grep $ID | grep -v grep | wc -l`'",'
					echo '  "fs_status":"'`grep proc /proc/mounts | grep ro, ; if [ -x /usr/bin/timeout.pl ] ; then timeout.pl 20 touch /var/log/monitor 2>&1 ; if [ -d /vservers/ ] ; then timeout.pl 20 touch /vservers/monitor.log 2>&1  ; fi ; fi`'",'
					echo '  "rpm_version":"'`if [ -x /usr/bin/timeout.pl ] ; then timeout.pl 30 rpm -q NodeManager ; fi`'",'
					echo '  "rpm_versions":"'`if [ -x /usr/bin/timeout.pl ] ; then timeout.pl 45 rpm -q -a ; fi`'",'
					echo "}"
EOF			""")

				values['ssh_error'] = errval
				if len(oval) > 0:
					#print "OVAL: %s" % oval
					values.update(eval(oval))
					values['ssh_portused'] = port
					break
				else:
					values.update({'kernel_version': "", 'bmlog' : "", 'bootcd_version' : '', 
									'nm_status' : '', 
									'fs_status' : '',
									'uptime' : '',
									'dns_status' : '',
									'rpm_version' : '',
									'rpm_versions' : '',
									'princeton_comon_dir' : "", 
									'princeton_comon_running' : "", 
									'princeton_comon_procs' : "", 'ssh_portused' : None})

			oval = values['nm_status']
			if "nm.py" in oval:
				values['nm_status'] = "Y"
			else:
				values['nm_status'] = "N"

			continue_slice_check = True
			oval = values['princeton_comon_dir']
			if "princeton_comon_dir" in oval:
				values['princeton_comon_dir'] = True
			else:
				values['princeton_comon_dir'] = False
				continue_slice_check = False

			if continue_slice_check:
				oval = values['princeton_comon_running']
				if len(oval) > len('/proc/virtual/'):
					values['princeton_comon_running'] = True
				else:
					values['princeton_comon_running'] = False
					continue_slice_check = False
			else:
				values['princeton_comon_running'] = False
				
			if continue_slice_check:
				oval = values['princeton_comon_procs']
				values['princeton_comon_procs'] = int(oval)
			else:
				values['princeton_comon_procs'] = None
		except:
			print traceback.print_exc()
			sys.exit(1)

		return values

	def collectPLC(self, nodename, cohash):
		values = {}
		### GET PLC NODE ######################
		d_node = plccache.GetNodeByName(nodename)
		values['plc_node_stats'] = d_node

		### GET PLC PCU ######################
		site_id = -1
		d_pcu = None
		if d_node and len(d_node['pcu_ids']) > 0:
			d_pcu = d_node['pcu_ids'][0]

		site_id = d_node['site_id']

		values['plc_pcuid'] = d_pcu

		### GET PLC SITE ######################
		print "SITEID: %s" % site_id
		d_site = plccache.GetSitesById([ site_id ])[0]
		values['loginbase'] = d_site['login_base']
		values['plc_site_stats'] = d_site 

		return values

	def evaluate(self, nodename, values):
		# TODO: this section can probably be reduced to a policy statement
		# 		using patterns and values collected so far.
		# NOTE: A node is "DOWN" if 
		#	* cannot ssh into it.
		#   * all ports are not open for a 'BOOT' node
		#   * dns for hostname does not exist.
		b_getbootcd_id = True

		oval = values['kernel_version']
		values['ssh_status'] = True
		if "2.6.17" in oval or "2.6.2" in oval:
			values['observed_category'] = 'PROD'
			if "bm.log" in values['bmlog']:
				values['observed_status'] = 'DEBUG'
			else:
				values['observed_status'] = 'BOOT'
		elif "2.6.12" in oval or "2.6.10" in oval:
			values['observed_category'] = 'OLDPROD'
			if "bm.log" in values['bmlog']:
				values['observed_status'] = 'DEBUG'
			else:
				values['observed_status'] = 'BOOT'
		
		# NOTE: on 2.6.8 kernels, with 4.2 bootstrapfs, the chroot 
		#	command fails.  I have no idea why.
		elif "2.4" in oval or "2.6.8" in oval:
			b_getbootcd_id = False
			values['observed_category'] = 'OLDBOOTCD'
			values['observed_status'] = 'DEBUG'
		elif oval != "":
			values['observed_category'] = 'UNKNOWN'
			if "bm.log" in values['bmlog']:
				values['observed_status'] = 'DEBUG'
			else:
				values['observed_status'] = 'BOOT'
		else:
			# An error occurred.
			b_getbootcd_id = False
			values['ssh_status'] = False
			values['observed_category'] = 'ERROR'
			values['observed_status'] = 'DOWN'
			values['kernel_version'] = ""

		values['firewall'] = False

		# NOTE: A node is down if some of the public ports are not open
		if values['observed_status'] == "BOOT":
			# verify that all ports are open.  Else, report node as down.
			if not ( values['port_status']['22']  == "open" and \
					 values['port_status']['80']  == "open" and \
					 values['port_status']['806'] == "open") :
				#email_exception(nodename, "%s FILTERED HOST" % nodename)
				values['observed_status'] = 'DOWN'
				values['firewall'] = True

			#if   values['port_status']['22']  == "open" and \
			#	 values['port_status']['80']  == "closed" and \
			#	 values['port_status']['806'] == "open" :
			#	email_exception("%s port 80 blocked" % nodename, "possible VSERVER ref blocked")

		#if not values['external_dns_status']:
		#	email_exception("%s DNS down" % nodename)

		if b_getbootcd_id:
			# try to get BootCD for all nodes that are not 2.4 nor inaccessible
			oval = values['bootcd_version']
			if "BootCD" in oval:
				values['bootcd_version'] = oval
				if "v2" in oval and \
					( nodename is not "planetlab1.cs.unc.edu" and \
					  nodename is not "planetlab2.cs.unc.edu" ):
					values['observed_category'] = 'OLDBOOTCD'
			else:
				values['bootcd_version'] = ""
		else:
			values['bootcd_version'] = ""

		return values

	def collectDNS(self, nodename, cohash):
		values = {}
		try:
			ipaddr = socket.gethostbyname(nodename)
			# TODO: check that IP returned matches IP in plc db.
			values['external_dns_status'] = True
		except Exception, err:
			values['external_dns_status'] = False

		return values

	def collectInternal(self, nodename, cohash):
		try:
			values = {}

			v = self.collectPING(nodename, cohash)
			values.update(v)

			v = self.collectPorts(nodename)
			values.update(v)

			v = self.collectSSH(nodename, cohash)
			values.update(v)

			v = self.collectDNS(nodename, cohash)
			values.update(v)

			v = self.collectTRACEROUTE(nodename, cohash)
			values.update(v)

			v = self.collectPLC(nodename, cohash)
			values.update(v)

			if nodename in cohash: 
				values['comon_stats'] = cohash[nodename]
			else:
				values['comon_stats'] = {'resptime':  '-1', 
										'uptime':    '-1',
										'sshstatus': '-1', 
										'lastcotop': '-1',
										'cpuspeed' : "null",
										'disksize' : 'null',
										'memsize'  : 'null'}

			values['rpms'] = values['rpm_versions']
			print "ALLVERSIONS: %s %s" % (nodename, values['rpm_versions'])
			print "RPMVERSION: %s %s" % (nodename, values['rpm_version'])
			print "UPTIME: %s %s" % (nodename, values['uptime'])

			values = self.evaluate(nodename, values)
			values['date_checked'] = datetime.now()

		except:
			print traceback.print_exc()

		return (nodename, values)


def internalprobe(hostname):
	scannode = ScanNodeInternal()
	try:
		(nodename, values) = scannode.collectInternal(hostname, {})
		scannode.record(None, (nodename, values))
		session.flush()
		return True
	except:
		print traceback.print_exc()
		return False

def externalprobe(hostname):
	scannode = ScanNodeInternal() 
	try:
		values = self.collectPorts(hostname)
		scannode.record(None, (hostname, values))
		session.flush()
		return True
	except:
		print traceback.print_exc()
		return False

class ScanPCU(ScanInterface):
	recordclass = FindbadPCURecord
	syncclass = None
	primarykey = 'plc_pcuid'

	def collectInternal(self, pcuname, cohash):

		continue_probe = True
		errors = None
		values = {'reboot_trial_status' : 'novalue'}
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

			#### RUN NMAP ###############################
			if continue_probe:
				nmap = command.CMD()
				print "nmap -oG - -P0 -p22,23,80,443,5869,9100,16992 %s | grep Host:" % reboot.pcu_name(values['plc_pcu_stats'])
				(oval,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,23,80,443,5869,9100,16992 %s | grep Host:" % reboot.pcu_name(values['plc_pcu_stats']))
				# NOTE: an empty / error value for oval, will still work.
				(values['port_status'], continue_probe) = nmap_port_status(oval)
			else:
				values['port_status'] = None
				
			#### COMPLETE ENTRY   #######################

			values['entry_complete'] = []
			#if values['protocol'] is None or values['protocol'] is "":
			#	values['entry_complete'] += ["protocol"]
			if values['plc_pcu_stats']['model'] is None or values['plc_pcu_stats']['model'] is "":
				values['entry_complete'] += ["model"]
				# Cannot continue due to this condition
				continue_probe = False

			if values['plc_pcu_stats']['password'] is None or values['plc_pcu_stats']['password'] is "":
				values['entry_complete'] += ["password"]
				# Cannot continue due to this condition
				continue_probe = False

			if len(values['entry_complete']) > 0:
				continue_probe = False

			if values['plc_pcu_stats']['hostname'] is None or values['plc_pcu_stats']['hostname'] is "":
				values['entry_complete'] += ["hostname"]
			if values['plc_pcu_stats']['ip'] is None or values['plc_pcu_stats']['ip'] is "":
				values['entry_complete'] += ["ip"]

			# If there are no nodes associated with this PCU, then we cannot continue.
			if len(values['plc_pcu_stats']['node_ids']) == 0:
				continue_probe = False
				values['entry_complete'] += ['nodeids']


			#### DNS and IP MATCH #######################
			if values['plc_pcu_stats']['hostname'] is not None and values['plc_pcu_stats']['hostname'] is not "" and \
			   values['plc_pcu_stats']['ip'] is not None and values['plc_pcu_stats']['ip'] is not "":
				try:
					ipaddr = socket.gethostbyname(values['plc_pcu_stats']['hostname'])
					if ipaddr == values['plc_pcu_stats']['ip']:
						values['dns_status'] = "DNS-OK"
					else:
						values['dns_status'] = "DNS-MISMATCH"
						values['plc_pcu_stats']['hostname'] = values['plc_pcu_stats']['ip']

				except Exception, err:
					values['dns_status'] = "DNS-NOENTRY"
					values['plc_pcu_stats']['hostname'] = values['plc_pcu_stats']['ip']
			else:
				if values['plc_pcu_stats']['ip'] is not None and values['plc_pcu_stats']['ip'] is not "":
					values['dns_status'] = "NOHOSTNAME"
					values['plc_pcu_stats']['hostname'] = values['plc_pcu_stats']['ip']
				else:
					values['dns_status'] = "NO-DNS-OR-IP"
					values['plc_pcu_stats']['hostname'] = "No_entry_in_DB"
					continue_probe = False


			######  DRY RUN  ############################
			if continue_probe and 'node_ids' in values['plc_pcu_stats'] and \
				len(values['plc_pcu_stats']['node_ids']) > 0:
				rb_ret = reboot.reboot_test_new(values['plc_pcu_stats']['nodenames'][0], 
												values, 1, True)
			else:
				rb_ret = "Not_Run" # No nodes to test"

			values['reboot_trial_status'] = rb_ret

		except:
			print "____________________________________"
			print values
			errors = values
			print "____________________________________"
			errors['traceback'] = traceback.format_exc()
			print errors['traceback']
			values['reboot_trial_status'] = str(errors['traceback'])
			print values

		values['entry_complete']=" ".join(values['entry_complete'])

		values['date_checked'] = datetime.now()
		return (pcuname, values)

