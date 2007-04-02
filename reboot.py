#!/usr/bin/python
#
# Reboot specified nodes
#

import getpass, getopt
import os, sys
import xml, xmlrpclib
import errno, time, traceback
import urllib2
import threading, popen2
import array, struct
from socket import *
import plc

# Use our versions of telnetlib and pyssh
sys.path.insert(0, os.path.dirname(sys.argv[0]))
import telnetlib
sys.path.insert(0, os.path.dirname(sys.argv[0]) + "/pyssh")    
import pyssh

# Timeouts in seconds
TELNET_TIMEOUT = 20

# Event class ID from pcu events
#NODE_POWER_CONTROL = 3

# Monitor user ID
#MONITOR_USER_ID = 11142

import logging
logger = logging.getLogger("monitor")
verbose = 1
dryrun = 0;

def telnet_answer(telnet, expected, buffer):
	global verbose

	output = telnet.read_until(expected, TELNET_TIMEOUT)
	if verbose:
		logger.debug(output)
	if output.find(expected) == -1:
		raise Exception, "'%s' not found" % expected
	else:
		telnet.write(buffer + "\r\n")


def ipal_reboot(ip, password, port):
	global dryrun, verbose

	telnet = None

	try:
		telnet = telnetlib.Telnet(ip, timeout=TELNET_TIMEOUT)
		telnet.set_debuglevel(verbose)

		# XXX Some iPals require you to hit Enter a few times first
		telnet_answer(telnet, "Password >", "\r\n\r\n")

		# Login
		telnet_answer(telnet, "Password >", password)

		# P# - Pulse relay
		if not dryrun:
			telnet_answer(telnet, "Enter >", "P%d" % port)

		telnet.read_until("Enter >", TELNET_TIMEOUT)

		# Close
		telnet.close()
		return 0

	except EOFError, err:
		if verbose:
			logger.debug(err)
		telnet.close()
		return errno.ECONNRESET
	except Exception, err:
		if verbose:
			logger.debug(err)
		if telnet:
			telnet.close()
		return errno.ETIMEDOUT


def apc_reboot(ip, username, password, port):
	global dryrun, verbose

	telnet = None

	try:
		telnet = telnetlib.Telnet(ip, timeout=TELNET_TIMEOUT)
		telnet.set_debuglevel(verbose)

		# Login
		telnet_answer(telnet, "User Name", username)
		telnet_answer(telnet, "Password", password)

		# 1- Device Manager
		# 2- Network
		# 3- System
		# 4- Logout

		# 1- Device Manager
		telnet_answer(telnet, "\r\n> ", "1")

		# 1- Phase Monitor/Configuration
		# 2- Outlet Restriction Configuration
		# 3- Outlet Control/Config
		# 4- Power Supply Status

		# 3- Outlet Control/Config
		telnet_answer(telnet, "\r\n> ", "3")

		# 1- Outlet 1
		# 2- Outlet 2
		# ...

		# n- Outlet n
		telnet_answer(telnet, "\r\n> ", str(port))
		
		# 1- Control Outlet
		# 2- Configure Outlet

		# 1- Control Outlet
		telnet_answer(telnet, "\r\n> ", "1")

		# 1- Immediate On			  
		# 2- Immediate Off			 
		# 3- Immediate Reboot		  
		# 4- Delayed On				
		# 5- Delayed Off			   
		# 6- Delayed Reboot			
		# 7- Cancel					

		# 3- Immediate Reboot		  
		telnet_answer(telnet, "\r\n> ", "3")

		if not dryrun:
			telnet_answer(telnet, 
				"Enter 'YES' to continue or <ENTER> to cancel", "YES\r\n")
			telnet_answer(telnet, 
				"Press <ENTER> to continue...", "")

		# Close
		telnet.close()
		return 0

	except EOFError, err:
		if verbose:
			logger.debug(err)
		if telnet:
			telnet.close()
		return errno.ECONNRESET
	except Exception, err:
		if verbose:
			logger.debug(err)
		if telnet:
			telnet.close()
		return errno.ETIMEDOUT


def baytech_reboot(ip, username, password, port):
	global dryrun, verbose

	ssh = None

	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.open()

		# Login
		telnet_answer(ssh, "password:", password)

		# PL1 comm output  (2 ,1).........1
		# PL2 comm output  (2 ,2).........2
		# PL3 comm output  (2 ,3).........3
		# no machine	   (2 ,4).........4
		# Control Outlets  (5 ,1).........5
		# Logout..........................T

		# Control Outlets  (5 ,1).........5
		telnet_answer(ssh, "Enter Request :", "5")

		# Reboot N
		telnet_answer(ssh, "DS-RPC>", "Reboot %d" % port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			telnet_answer(ssh, "(Y/N)?", "N")
		else:
			telnet_answer(ssh, "(Y/N)?", "Y")
		telnet_answer(ssh, "DS-RPC>", "")

		# Close
		output = ssh.close()
		if verbose:
			logger.debug(err)
		return 0

	except Exception, err:
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return errno.ETIMEDOUT

### rebooting european BlackBox PSE boxes
# Thierry Parmentelat - May 11 2005
# tested on 4-ports models known as PSE505-FR
# uses http to POST a data 'P<port>=r'
# relies on basic authentication within http1.0
# first curl-based script was
# curl --http1.0 --basic --user <username>:<password> --data P<port>=r \
#	http://<hostname>:<http_port>/cmd.html && echo OK

def bbpse_reboot (pcu_ip,username,password,port_in_pcu,http_port):

	global dryrun, verbose

	url = "http://%s:%d/cmd.html" % (pcu_ip,http_port)
	data= "P%d=r" % port_in_pcu
	if verbose:
		logger.debug("POSTing '%s' on %s" % (data,url))

	authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
	uri = "%s:%d" % (pcu_ip,http_port)
	authinfo.add_password (None, uri, username, password)
	authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)

	if (dryrun):
		return 0

	try:
		f = urllib2.urlopen(url,data)

		r= f.read()
		if verbose:
			logger.debug(r)
		return 0

	except urllib2.URLError,err:
		logger.info('Could not open http connection', err)
		return -1

### rebooting x10toggle based systems addressed by port
# Marc E. Fiuczynski - May 31 2005
# tested on 4-ports models known as PSE505-FR
# uses ssh and password to login to an account
# that will cause the system to be powercycled.

def x10toggle_reboot(ip, username, password, port):
	global dryrun, verbose

	ssh = None
	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.open()

		# Login
		telnet_answer(ssh, "password:", password)

		if not dryrun:
			# Reboot
			telnet_answer(ssh, "x10toggle>", "A%d" % port)

		# Close
		output = ssh.close()
		if verbose:
			logger.debug(output)
		return 0

	except Exception, err:
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(output)
		return errno.ETIMEDOUT

### rebooting Dell systems via RAC card
# Marc E. Fiuczynski - June 01 2005
# tested with David Lowenthal's itchy/scratchy nodes at UGA
#

def runcmd(command, args, username, password, timeout = None):

	result = [None]
	result_ready = threading.Condition()

	def set_result(x):

		result_ready.acquire()
		try:
			result[0] = x
		finally:
			result_ready.notify()
			result_ready.release()

	def do_command(command, username, password):

		try:
			# Popen4 is a popen-type class that combines stdout and stderr
			p = popen2.Popen4(command)

			# read all output data
			p.tochild.write("%s\n" % username)
			p.tochild.write("%s\n" % password)
			p.tochild.close()
			data = p.fromchild.read()

			while True:
				# might get interrupted by a signal in poll() or waitpid()
				try:
					retval = p.wait()
					set_result((retval, data))
					break
				except OSError, ex:
					if ex.errno == errno.EINTR:
						continue
					raise ex
		except Exception, ex:
			set_result(ex)

	if args:
		command = " ".join([command] + args)

	worker = threading.Thread(target = do_command, args = (command, username, password, ))
	worker.setDaemon(True)
	result_ready.acquire()
	worker.start()
	result_ready.wait(timeout)
	try:
		if result == [None]:
			raise Exception, "command timed-out: '%s'" % command
	finally:
		result_ready.release()
	result = result[0]

	if isinstance(result, Exception):
		raise result
	else:
		(retval, data) = result
		if os.WIFEXITED(retval) and os.WEXITSTATUS(retval) == 0:
			return data
		else:
			out = "system command ('%s') " % command
			if os.WIFEXITED(retval):
				out += "failed, rc = %d" % os.WEXITSTATUS(retval)
			else:
				out += "killed by signal %d" % os.WTERMSIG(retval)
			if data:
				out += "; output follows:\n" + data
			raise Exception, out

def racadm_reboot(ip, username, password, port):
	global dryrun, verbose

	try:
		cmd = "/usr/sbin/racadm"
		os.stat(cmd)
		if not dryrun:
			output = runcmd(cmd, ["-r %s -i serveraction powercycle" % ip],
				username, password)
		else:
			output = "dryrun of racadm command"

		logger.debug("runcmd returned without output %s" % output)
		if verbose:
			logger.debug(output)
		return 0

	except Exception, err:
		logger.debug("runcmd raised exception %s" % err)
		if verbose:
			logger.debug(err)
		return errno.ETIMEDOUT

# Returns true if rebooted via PCU
def reboot(nodename):
	pcu = plc.getpcu(nodename)
	if not pcu:
		plc.nodePOD(nodename)
		return False
	# Try the PCU first
	logger.debug("Trying PCU %s %s" % (pcu['hostname'], pcu['model']))

	# APC Masterswitch (Berkeley)
	if pcu['protocol'] == "telnet" and pcu['model'] == "APC Masterswitch":
		err = apc_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu[nodename])

	# DataProbe iPal (many sites)
	elif pcu['protocol'] == "telnet" and pcu['model'].find("IP-4") >= 0:
		err = ipal_reboot(pcu['ip'],pcu['password'], pcu[nodename])

	# BayTech DS4-RPC
	elif pcu['protocol'] == "ssh" and \
	(pcu['model'].find("Baytech") >= 0 or pcu['model'].find("DS4") >= 0):
		err = baytech_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu[nodename])

	# BlackBox PSExxx-xx (e.g. PSE505-FR)
	elif pcu['protocol'] == "http" and (pcu['model'] == "bbpse"):
		err = bbpse_reboot(pcu['ip'], pcu['username'], pcu['password'], pcu[nodename],80)

	# x10toggle
	elif pcu['protocol'] == "ssh" and (pcu['model'] == "x10toggle"):
		err = x10toggle_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu[nodename])

	# x10toggle
	elif pcu['protocol'] == "racadm" and (pcu['model'] == "RAC"):
		err = racadm_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu_[nodename])

	# Unknown or unsupported
	else:
		err = errno.EPROTONOSUPPORT
		return False
	return True 

#def get_suggested(suggestion_id,db):
#
#	sql= """select node_id,pcu_id from nodes where suggestion = %d """\
#			% (suggestion_id)
#	try:
#		nodes = db.query(sql).dictresult()
#	except pg.ProgrammingError, err:
#		print( "Database error for query: %s\n%s" % (sql,err) )
#		sys.exit(1)
#	return nodes

#def get_pcu_info(node_id,pcu_id,db):
#	sql= """select port_number from pcu_ports where node_id = %d and pcu_id = %d """\
#			% (node_id,pcu_id)
#	try:
#	   port_number = db.query(sql).dictresult()
#	except pg.ProgrammingError, err:
#		print( "Database error for query: %s\n%s" % (sql,err) )
#		sys.exit(1)
#	
#	sql= """select * from pcu where pcu_id = %d """\
#			% (pcu_id)
#	try:
#		pcu = db.query(sql).dictresult()
#	except pg.ProgrammingError, err:
#		print( "Database error for query: %s\n%s" % (sql,err) )
#		sys.exit(1)
#
#	result = {'node_id':node_id,'pcu_id':pcu_id,'port_number':port_number[0]['port_number'], 
#			  'ip':pcu[0]['ip'],'username':pcu[0]['username'],'password':pcu[0]['password'],\
#			  'model':pcu[0]['model'],'protocol':pcu[0]['protocol'],'hostname':pcu[0]['hostname']}
#
#	return result

#def add_plc_event(node_id,err,db):
#	site_id = plc_db_utils.get_site_from_node_id(node_id,db)
#	message = "PCU reboot by monitor-msgs@planet-lab.org: %s" % os.strerror(err)
#
#	sql = """insert into events (event_class_id,message,person_id,node_id,site_id) values """\
#		  """(%d,'%s',%d,%d,%d)""" % (NODE_POWER_CONTROL,message,MONITOR_USER_ID,node_id,site_id)
#	print sql
#
#	try:
#		db.query(sql)
#	except pg.ProgrammingError, err:
#		print( "Database error for: %s\n%s" % (sql,err) )
#		sys.exit(1)


def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('LOGGER - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)


	try:
		reboot("planetlab2.cs.uchicago.edu")
		reboot("alice.cs.princeton.edu")
	except Exception, err:
		print err
	# used later for pretty printing
#	pp = pprint.PrettyPrinter(indent=2)

#	user = "Monitor"
#	password = None

#	plc_db = plc_dbs.open_plc_db_write()
#	mon_db = plc_dbs.open_mon_db()

	# 5 = needs script reboot - fix this later
#	nodes = get_suggested(5,mon_db)

#	for row in nodes:
		
#		pcu = get_pcu_info(row['node_id'],row['pcu_id'],plc_db)
#		add_plc_event(row['node_id'],err,plc_db)

if __name__ == '__main__':
	import plc
	logger = logging.getLogger("monitor")
	main()
