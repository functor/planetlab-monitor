#!/usr/bin/python

import os
import sys
import string
import time
from datetime import datetime,timedelta
import threadpool
import threading

from monitor import util
from monitor.util import command
from monitor import config

from monitor.database.info.model import FindbadNodeRecordSync, FindbadNodeRecord, session

from monitor.sources import comon
from monitor.wrapper import plc, plccache

from nodequery import verify,query_to_dict,node_select
import traceback
from nodecommon import nmap_port_status

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

def collectNMAP(nodename, cohash):
	#### RUN NMAP ###############################
	values = {}
	nmap = util.command.CMD()
	print "nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename
	(oval,eval) = nmap.run_noexcept("nmap -oG - -P0 -p22,80,806 %s | grep Host:" % nodename)
	# NOTE: an empty / error value for oval, will still work.
	(values['port_status'], continue_probe) = nmap_port_status(oval)

	values['date_checked'] = datetime.now()
			
	return (nodename, values)

def collectPingAndSSH(nodename, cohash):
	### RUN PING ######################
	ping = command.CMD()
	(oval,errval) = ping.run_noexcept("ping -c 1 -q %s | grep rtt" % nodename)

	try:
		values = {}

		if oval == "":
			# An error occurred
			values['ping_status'] = False
		else:
			values['ping_status'] = True

		try:
			for port in [22, 806]: 
				ssh = command.SSH('root', nodename, port)

				(oval, errval) = ssh.run_noexcept2(""" <<\EOF
					echo "{"
					echo '  "kernel_version":"'`uname -a`'",'
					echo '  "bmlog":"'`ls /tmp/bm.log`'",'
					echo '  "bootcd_version":"'`cat /mnt/cdrom/bootme/ID`'",'
					echo '  "nm_status":"'`ps ax | grep nm.py | grep -v grep`'",'
					echo '  "fs_status":"'`touch /var/log/monitor 2>&1`'",'
					echo '  "dns_status":"'`host boot.planet-lab.org 2>&1`'",'
					echo '  "princeton_comon_dir":"'`ls -d /vservers/princeton_comon`'",'

					ID=`grep princeton_comon /etc/passwd | awk -F : '{if ( $3 > 500 ) { print $3}}'` 
					echo '  "princeton_comon_running":"'`ls -d /proc/virtual/$ID`'",'
					echo '  "princeton_comon_procs":"'`vps ax | grep $ID | grep -v grep | wc -l`'",'
					echo "}"
EOF				""")
				
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
									'dns_status' : '',
									'princeton_comon_dir' : "", 
									'princeton_comon_running' : "", 
									'princeton_comon_procs' : "", 'ssh_portused' : None})
		except:
			print traceback.print_exc()
			sys.exit(1)

		### RUN SSH ######################
		b_getbootcd_id = True
		#ssh = command.SSH('root', nodename)
		#oval = ""
		#errval = ""
		#(oval, errval) = ssh.run_noexcept('echo `uname -a ; ls /tmp/bm.log`')

		oval = values['kernel_version']
		if "2.6.17" in oval or "2.6.2" in oval:
			values['ssh_status'] = True
			values['observed_category'] = 'PROD'
			if "bm.log" in values['bmlog']:
				values['observed_status'] = 'DEBUG'
			else:
				values['observed_status'] = 'BOOT'
		elif "2.6.12" in oval or "2.6.10" in oval:
			values['ssh_status'] = True
			values['observed_category'] = 'OLDPROD'
			if "bm.log" in values['bmlog']:
				values['observed_status'] = 'DEBUG'
			else:
				values['observed_status'] = 'BOOT'
		
		# NOTE: on 2.6.8 kernels, with 4.2 bootstrapfs, the chroot command fails.  I have no idea why.
		elif "2.4" in oval or "2.6.8" in oval:
			b_getbootcd_id = False
			values['ssh_status'] = True
			values['observed_category'] = 'OLDBOOTCD'
			values['observed_status'] = 'DEBUG'
		elif oval != "":
			values['ssh_status'] = True
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
			val = errval.strip()
			values['ssh_error'] = val
			values['kernel_version'] = ""

		#values['kernel_version'] = val

		if b_getbootcd_id:
			# try to get BootCD for all nodes that are not 2.4 nor inaccessible
			#(oval, errval) = ssh.run_noexcept('cat /mnt/cdrom/bootme/ID')
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

		# TODO: get bm.log for debug nodes.
		# 'zcat /tmp/bm.log'
		
		#(oval, errval) = ssh.run_noexcept('ps ax | grep nm.py | grep -v grep')
		oval = values['nm_status']
		if "nm.py" in oval:
			values['nm_status'] = "Y"
		else:
			values['nm_status'] = "N"

		continue_slice_check = True
		#(oval, errval) = ssh.run_noexcept('ls -d /vservers/princeton_comon')
		oval = values['princeton_comon_dir']
		if "princeton_comon_dir" in oval:
			values['princeton_comon_dir'] = True
		else:
			values['princeton_comon_dir'] = False
			continue_slice_check = False

		if continue_slice_check:
			#(oval, errval) = ssh.run_noexcept('ID=`grep princeton_comon /etc/passwd | awk -F : "{if ( \\\$3 > 500 ) { print \\\$3}}"`; ls -d /proc/virtual/$ID')
			oval = values['princeton_comon_running']
			if len(oval) > len('/proc/virtual/'):
				values['princeton_comon_running'] = True
			else:
				values['princeton_comon_running'] = False
				continue_slice_check = False
		else:
			values['princeton_comon_running'] = False
			
		if continue_slice_check:
			#(oval, errval) = ssh.run_noexcept('ID=`grep princeton_comon /etc/passwd | awk -F : "{if ( \\\$3 > 500 ) { print \\\$3}}"`; vps ax | grep $ID | grep -v grep | wc -l')
			oval = values['princeton_comon_procs']
			values['princeton_comon_procs'] = int(oval)
		else:
			values['princeton_comon_procs'] = None

			
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
		# include output value
		### GET PLC NODE ######################
		plc_lock.acquire()
		d_node = None
		try:
			d_node = plc.getNodes({'hostname': nodename}, ['pcu_ids', 'site_id', 'date_created', 
									'last_updated', 'last_contact', 'boot_state', 'nodegroup_ids'])[0]
		except:
			traceback.print_exc()
		plc_lock.release()
		values['plc_node_stats'] = d_node

		##### NMAP  ###################
		(n, v) = collectNMAP(nodename, None)
		values.update(v)

		### GET PLC PCU ######################
		site_id = -1
		d_pcu = None
		if d_node:
			pcu = d_node['pcu_ids']
			if len(pcu) > 0:
				d_pcu = pcu[0]

			site_id = d_node['site_id']

		values['plc_pcuid'] = d_pcu

		### GET PLC SITE ######################
		plc_lock.acquire()
		d_site = None
		values['loginbase'] = ""
		try:
			d_site = plc.getSites({'site_id': site_id}, 
								['max_slices', 'slice_ids', 'node_ids', 'login_base'])[0]
			values['loginbase'] = d_site['login_base']
		except:
			traceback.print_exc()
		plc_lock.release()

		values['plc_site_stats'] = d_site 
		values['date_checked'] = datetime.now()
	except:
		print traceback.print_exc()

	return (nodename, values)

def recordPingAndSSH(request, result):
	global global_round
	global count
	(nodename, values) = result

	try:
		if values is not None:
			#fbsync = FindbadNodeRecordSync.findby_or_create(hostname="global", 
			#												if_new_set={'round' : global_round})
			#global_round = fbsync.round
			fbnodesync = FindbadNodeRecordSync.findby_or_create(hostname=nodename,
															if_new_set={'round' : global_round})

			# NOTE: This code will either add a new record for the new global_round, 
			# 		OR it will find the previous value, and update it
			# 		with new information.
			#		The data that is 'lost' is not that important, b/c older
			#		history still exists.  
			fbrec = FindbadNodeRecord.findby_or_create(
						round=global_round,
						hostname=nodename)

			fbrec.set(  **values ) 
						#date_checked=values['date_checked'],
			  			#loginbase=values['loginbase'],
			  			#kernel_version=values['kernel_version'],
			  			#bootcd_version=values['bootcd_version'],
			  			#nm_status=values['nm_status'],
			  			#fs_status=values['fs_status'],
			  			#dns_status=values['dns_status'],
			  			#princeton_comon_dir=values['princeton_comon_dir'],
			  			#princeton_comon_running=values['princeton_comon_running'],
			  			#princeton_comon_procs=values['princeton_comon_procs'],
			  			#plc_node_stats = values['plc_node_stats'],
			  			#plc_site_stats = values['plc_site_stats'],
			  			#plc_pcuid = values['plc_pcuid'],
			  			#comon_stats = values['comon_stats'],
			  			#ping_status = values['ping_status'],
			  			#ssh_portused = values['ssh_portused'],
			  			#ssh_status = values['ssh_status'],
			  			#ssh_error = values['ssh_error'],
			  			#observed_status = values['observed_status'],
			  			#observed_category = values['observed_category'])

			#for v in before.keys():
			#	if before[v] == after[v]:
			#		print "SAME FOR KEY %s" % v
			#	print "%s : %s\t%s" % ( v, before[v], after[v] )

			fbrec.flush()
			fbnodesync.round = global_round
			fbnodesync.flush()
			#fbsync.flush()

			count += 1
			print "%d %s %s" % (count, nodename, values)
	except:
		print "ERROR:"
		print traceback.print_exc()

# this will be called when an exception occurs within a thread
def handle_exception(request, result):
	print "Exception occured in request %s" % request.requestID
	for i in result:
		print "Result: %s" % i

def externalprobe(hostname):
	try:
		(nodename, values) = collectNMAP(hostname, {})
		recordPingAndSSH(None, (nodename, values))
		session.flush()
		return True
	except:
		print traceback.print_exc()
		return False

def probe(hostname):
	try:
		(nodename, values) = collectPingAndSSH(hostname, {})
		recordPingAndSSH(None, (nodename, values))
		session.flush()
		return True
	except:
		print traceback.print_exc()
		return False
		

def checkAndRecordState(l_nodes, cohash):
	global global_round
	global count

	tp = threadpool.ThreadPool(20)

	# CREATE all the work requests
	for nodename in l_nodes:
		fbnodesync = FindbadNodeRecordSync.findby_or_create(hostname=nodename, if_new_set={'round':0})
		node_round   = fbnodesync.round
		fbnodesync.flush()

		if node_round < global_round or config.force:
			# recreate node stats when refreshed
			#print "%s" % nodename
			req = threadpool.WorkRequest(collectPingAndSSH, [nodename, cohash], {}, 
										 None, recordPingAndSSH, handle_exception)
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

	print FindbadNodeRecordSync.query.count()
	print FindbadNodeRecord.query.count()
	session.flush()

def main():
	global global_round

	fbsync = FindbadNodeRecordSync.findby_or_create(hostname="global", 
													if_new_set={'round' : global_round})
	global_round = fbsync.round

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
		f_nodes = util.file.getListFromFile(config.nodelist)
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
		fbsync.round = global_round
		fbsync.flush()

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
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
	print "sleeping"
	#print "final commit"
	#time.sleep(10)
