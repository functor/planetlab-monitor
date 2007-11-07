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
#from socket import *
import socket
import plc

plc_lock = threading.Lock()

# Use our versions of telnetlib and pyssh
sys.path.insert(0, os.path.dirname(sys.argv[0]))
import telnetlib
sys.path.insert(0, os.path.dirname(sys.argv[0]) + "/pyssh")    
import pyssh

# Timeouts in seconds
TELNET_TIMEOUT = 30

# Event class ID from pcu events
#NODE_POWER_CONTROL = 3

# Monitor user ID
#MONITOR_USER_ID = 11142

import logging
logger = logging.getLogger("monitor")
verbose = 1
#dryrun = 0;

class ExceptionNotFound(Exception): pass
class ExceptionPassword(Exception): pass
class ExceptionTimeout(Exception): pass
class ExceptionPrompt(Exception): pass
class ExceptionPort(Exception): pass

def telnet_answer(telnet, expected, buffer):
	global verbose

	output = telnet.read_until(expected, TELNET_TIMEOUT)
	#if verbose:
	#	logger.debug(output)
	if output.find(expected) == -1:
		raise ExceptionNotFound, "'%s' not found" % expected
	else:
		telnet.write(buffer + "\r\n")


# PCU has model, host, preferred-port, user, passwd, 

class PCUExpect:
	def __init__(self, protocol, verbose, dryrun):
		self.verbose = verbose
		self.protocol = protocol
		self.dryrun = dryrun

	def telnet_answer(telnet, expected, buffer):
		global verbose

		output = telnet.read_until(expected, TELNET_TIMEOUT)
		#if verbose:
		#	logger.debug(output)
		if output.find(expected) == -1:
			raise ExceptionNotFound, "'%s' not found" % expected
		else:
			telnet.write(buffer + "\r\n")
	
	def _run(self, host, user, passwd, node_port, protocols):
		self.run()

	def run(self):
		pass
		
	

def ipal_reboot(ip, password, port, dryrun):
	global verbose
	global plc_lock


	telnet = None

	try:
		#plc_lock.acquire()
		#print "lock acquired"

		#try:
			#telnet = telnetlib.Telnet(ip) # , timeout=TELNET_TIMEOUT)
		telnet = telnetlib.Telnet(ip, timeout=TELNET_TIMEOUT)
		#except:
		#	import traceback
		#	traceback.print_exc()


		telnet.set_debuglevel(verbose)

		# XXX Some iPals require you to hit Enter a few times first
		telnet_answer(telnet, "Password >", "\r\n\r\n")

		# Login
		telnet_answer(telnet, "Password >", password)

		# XXX Some iPals require you to hit Enter a few times first
		telnet.write("\r\n\r\n")

		# P# - Pulse relay
		if not dryrun:
			telnet_answer(telnet, "Enter >", "P%d" % port)

		telnet.read_until("Enter >", TELNET_TIMEOUT)

		# Close
		telnet.close()

		#print "lock released"
		#plc_lock.release()
		return 0

	except EOFError, err:
		if verbose:
			logger.debug("ipal_reboot: EOF")
			logger.debug(err)
		telnet.close()
		import traceback
		traceback.print_exc()
		#print "lock released"
		#plc_lock.release()
		return errno.ECONNRESET
	except socket.error, err:
		logger.debug("ipal_reboot: Socket Error")
		logger.debug(err)
		import traceback
		traceback.print_exc()

		return errno.ETIMEDOUT
		
	except Exception, err:
		if verbose:
			logger.debug("ipal_reboot: Exception")
			logger.debug(err)
		if telnet:
			telnet.close()
		import traceback
		traceback.print_exc()
		#print "lock released"
		#plc_lock.release()
		return  "ipal error"


def apc_reboot(ip, username, password, port, protocol, dryrun):
	global verbose

	transport = None

	try:
		#if "ssh" in protocol:
		if "22" in protocol and protocol['22'] == "open":
			transport = pyssh.Ssh(username, ip)
			transport.open()
			# Login
			telnet_answer(transport, "password:", password)
		#elif "telnet" in protocol:
		elif "23" in protocol and protocol['23'] == "open":
			transport = telnetlib.Telnet(ip, timeout=TELNET_TIMEOUT)
			#transport = telnetlib.Telnet(ip)
			transport.set_debuglevel(verbose)
			# Login
			telnet_answer(transport, "User Name", username)
			telnet_answer(transport, "Password", password)
		else:
			logger.debug("Unknown protocol %s" %protocol)
			raise "Closed protocol ports!"


		# 1- Device Manager
		# 2- Network
		# 3- System
		# 4- Logout

		# 1- Device Manager
		telnet_answer(transport, "\r\n> ", "1")

		# 1- Phase Monitor/Configuration
		# 2- Outlet Restriction Configuration
		# 3- Outlet Control/Config
		# 4- Power Supply Status

		# 3- Outlet Control/Config
		telnet_answer(transport, "\r\n> ", "3")

		# 1- Outlet 1
		# 2- Outlet 2
		# ...

		# n- Outlet n
		telnet_answer(transport, "\r\n> ", str(port))
		
		# 1- Control Outlet
		# 2- Configure Outlet

		# 1- Control Outlet
		telnet_answer(transport, "\r\n> ", "1")

		# 1- Immediate On			  
		# 2- Immediate Off			 
		# 3- Immediate Reboot		  
		# 4- Delayed On				
		# 5- Delayed Off			   
		# 6- Delayed Reboot			
		# 7- Cancel					

		# 3- Immediate Reboot		  
		telnet_answer(transport, "\r\n> ", "3")

		if not dryrun:
			telnet_answer(transport, 
				"Enter 'YES' to continue or <ENTER> to cancel", "YES\r\n")
			telnet_answer(transport, 
				"Press <ENTER> to continue...", "")

		# Close
		transport.close()
		return 0

	except EOFError, err:
		if verbose:
			logger.debug(err)
		if transport:
			transport.close()
		return errno.ECONNRESET
	except socket.error, err:
		if verbose:
			logger.debug(err)
		return errno.ETIMEDOUT

	except Exception, err:
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if transport:
			transport.close()
		return "apc error: check password"

def drac_reboot(ip, username, password, dryrun):
	global verbose
	ssh = None
	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.set_debuglevel(verbose)
		ssh.open()
		# Login
		print "password"
		telnet_answer(ssh, "password:", password)

		# Testing Reboot ?
		print "reset or power"
		if dryrun:
			telnet_answer(ssh, "[%s]#" % username, "getsysinfo")
		else:
			# Reset this machine
			telnet_answer(ssh, "[%s]#" % username, "serveraction powercycle")

		print "exit"
		telnet_answer(ssh, "[%s]#" % username, "exit")

		# Close
		print "close"
		output = ssh.close()
		return 0

	except socket.error, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return errno.ETIMEDOUT
	except Exception, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return "drac error: check password"

def ilo_reboot(ip, username, password, dryrun):
	global verbose

	ssh = None

	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.set_debuglevel(verbose)
		ssh.open()
		# Login
		print "password"
		telnet_answer(ssh, "password:", password)

		# User:vici logged-in to ILOUSE701N7N4.CS.Princeton.EDU(128.112.154.171)
		# iLO Advanced 1.26 at 10:01:40 Nov 17 2006
		# Server Name: USE701N7N400
		# Server Power: On
		# 
		# </>hpiLO-> 
		print "cd system1"
		telnet_answer(ssh, "</>hpiLO->", "cd system1")

		# Reboot Outlet  N	  (Y/N)?
		print "reset or power"
		if dryrun:
			telnet_answer(ssh, "</system1>hpiLO->", "POWER")
		else:
			# Reset this machine
			telnet_answer(ssh, "</system1>hpiLO->", "reset")

		print "exit"
		telnet_answer(ssh, "</system1>hpiLO->", "exit")

		# Close
		print "close"
		output = ssh.close()
		return 0

	except socket.error, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return errno.ETIMEDOUT
	except Exception, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return "ilo error: check password"

def baytech_reboot(ip, username, password, port, dryrun):
	global verbose

	ssh = None

	#verbose = 1 
	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.set_debuglevel(verbose)
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
		try:
			telnet_answer(ssh, "DS-RPC>", "Reboot %d" % port)
		except ExceptionNotFound, msg:
			# one machine is configured to ask for a username,
			# even after login...
			print "msg: %s" % msg
			ssh.write(username + "\r\n")
			telnet_answer(ssh, "DS-RPC>", "Reboot %d" % port)
			

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			telnet_answer(ssh, "(Y/N)?", "N")
		else:
			telnet_answer(ssh, "(Y/N)?", "Y")
		telnet_answer(ssh, "DS-RPC>", "")

		# Close
		output = ssh.close()
		return 0

	except socket.error, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return errno.ETIMEDOUT
	except Exception, err:
		print "exception"
		import traceback
		traceback.print_exc()
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(err)
		return "baytech error: check password"

### rebooting european BlackBox PSE boxes
# Thierry Parmentelat - May 11 2005
# tested on 4-ports models known as PSE505-FR
# uses http to POST a data 'P<port>=r'
# relies on basic authentication within http1.0
# first curl-based script was
# curl --http1.0 --basic --user <username>:<password> --data P<port>=r \
#	http://<hostname>:<http_port>/cmd.html && echo OK

def bbpse_reboot (pcu_ip,username,password,port_in_pcu,http_port, dryrun):

	global verbose

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
		return "bbpse error"

### rebooting x10toggle based systems addressed by port
# Marc E. Fiuczynski - May 31 2005
# tested on 4-ports models known as PSE505-FR
# uses ssh and password to login to an account
# that will cause the system to be powercycled.

def x10toggle_reboot(ip, username, password, port, dryrun):
	global verbose

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

def racadm_reboot(ip, username, password, port, dryrun):
	global verbose

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

def pcu_name(pcu):
	if pcu['hostname'] is not None and pcu['hostname'] is not "":
		return pcu['hostname']
	elif pcu['ip'] is not None and pcu['ip'] is not "":
		return pcu['ip']
	else:
		return None

def get_pcu_values(pcu_id):
	# TODO: obviously, this shouldn't be loaded each time...
	import soltesz
	fb =soltesz.dbLoad("findbadpcus")

	try:
		values = fb['nodes']["id_%s" % pcu_id]['values']
	except:
		values = None

	return values

def reboot_new(nodename, continue_probe, dryrun):

	pcu = plc.getpcu(nodename)
	if not pcu:
		return False

	values = get_pcu_values(pcu['pcu_id'])
	if values == None:
		return False
	
	# Try the PCU first
	logger.debug("Trying PCU %s %s" % (pcu['hostname'], pcu['model']))

	# DataProbe iPal (many sites)
	if  continue_probe and values['model'].find("Dataprobe IP-41x/IP-81x") >= 0:
		if values['portstatus']['23'] == "open":
			rb_ret = ipal_reboot(pcu_name(values),
									values['password'],
									pcu[nodename],
									dryrun)
		else:
			rb_ret = "Unsupported_Port"
			

	# APC Masterswitch (Berkeley)
	elif continue_probe and values['model'].find("APC AP79xx/Masterswitch") >= 0:
		if  values['portstatus']['22'] == "open" or \
			values['portstatus']['23'] == "open":
			rb_ret = apc_reboot(pcu_name(values),
									values['username'],
									values['password'], 
									pcu[nodename],
									values['portstatus'], 
									dryrun)
		else:
			rb_ret = "Unsupported_Port"
	# BayTech DS4-RPC
	elif continue_probe and values['model'].find("Baytech DS4-RPC") >= 0:
		if values['portstatus']['22'] == "open":
			rb_ret = baytech_reboot(pcu_name(values),
									   values['username'],
									   values['password'], 
									   pcu[nodename],
									   dryrun)
		else:
			rb_ret = "Unsupported_Port"
			

	# iLO
	elif continue_probe and values['model'].find("HP iLO") >= 0:
		if values['portstatus']['22'] == "open":
			rb_ret = ilo_reboot(pcu_name(values),
									   values['username'],
									   values['password'], 
									   dryrun)
		else:
			rb_ret = "Unsupported_Port"
			
	# DRAC ssh
	elif continue_probe and values['model'].find("Dell RAC") >= 0:
		if values['portstatus']['22'] == "open":
			rb_ret = drac_reboot(pcu_name(values),
									   values['username'],
									   values['password'], 
									   dryrun)
		else:
			rb_ret = "Unsupported_Port"
			

	# BlackBox PSExxx-xx (e.g. PSE505-FR)
	elif continue_probe and \
		(values['model'].find("BlackBox PS5xx") >= 0 or
		 values['model'].find("ePowerSwitch 1/4/8x") >=0 ):
		if values['portstatus']['80'] == "open":
			rb_ret = bbpse_reboot(pcu_name(values),
							values['username'], 
							values['password'], 
							pcu[nodename],
							80,
							dryrun)
		else:
			rb_ret = "Unsupported_PCU"
			
	# x10toggle
	elif 	continue_probe and values['protocol'] == "ssh" and \
			values['model'] == "x10toggle":
		rb_ret = x10toggle_reboot(pcu_name(values),
										values['username'],
										values['password'], 
										pcu[nodename],
										dryrun)
	# ????
	elif continue_probe and values['protocol'] == "racadm" and \
			values['model'] == "RAC":
		rb_ret = racadm_reboot(pcu_name(values),
									  values['username'],
									  values['password'],
									  pcu[nodename],
									  dryrun)
	elif continue_probe:
		rb_ret = "Unsupported_PCU"

	elif continue_probe == False:
		if 'portstatus' in values:
			rb_ret = "NetDown"
		else:
			rb_ret = "Not_Run"
	else:
		rb_ret = -1
	
	if rb_ret != 0:
		return False
	else:
		return True


# Returns true if rebooted via PCU
def reboot(nodename, dryrun):
	pcu = plc.getpcu(nodename)
	if not pcu:
		plc.nodePOD(nodename)
		return False
	# Try the PCU first
	logger.debug("Trying PCU %s %s" % (pcu['hostname'], pcu['model']))

	# APC Masterswitch (Berkeley)
	if pcu['model'] == "APC Masterswitch":
		err = apc_reboot(pcu['ip'], pcu['username'],pcu['password'], 
				pcu[nodename], pcu['protocol'], dryrun)

	# DataProbe iPal (many sites)
	elif pcu['protocol'] == "telnet" and pcu['model'].find("IP-4") >= 0:
		err = ipal_reboot(pcu['ip'],pcu['password'], pcu[nodename], dryrun)

	# BayTech DS4-RPC
	elif pcu['protocol'] == "ssh" and \
	(pcu['model'].find("Baytech") >= 0 or pcu['model'].find("DS4") >= 0):
		err = baytech_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu[nodename], dryrun)

	# BlackBox PSExxx-xx (e.g. PSE505-FR)
	elif pcu['protocol'] == "http" and (pcu['model'] == "bbpse"):
		err = bbpse_reboot(pcu['ip'], pcu['username'], pcu['password'], pcu[nodename],80, dryrun)

	# x10toggle
	elif pcu['protocol'] == "ssh" and (pcu['model'] == "x10toggle"):
		err = x10toggle_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu[nodename], dryrun)

	# 
	elif pcu['protocol'] == "racadm" and (pcu['model'] == "RAC"):
		err = racadm_reboot(pcu['ip'], pcu['username'],pcu['password'], pcu_[nodename], dryrun)

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
