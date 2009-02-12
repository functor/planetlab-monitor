#!/usr/bin/python
#
# Reboot specified nodes
#

import getpass, getopt
import os, sys
import xml, xmlrpclib
import errno, time, traceback
import urllib2
import urllib
import threading, popen2
import array, struct
from monitor.wrapper import plc
import base64
from subprocess import PIPE, Popen
import pcucontrol.transports.ssh.pxssh as pxssh
import pcucontrol.transports.ssh.pexpect as pexpect
import socket
from monitor.util import command


# Use our versions of telnetlib and pyssh
sys.path.insert(0, os.path.dirname(sys.argv[0]))
import pcucontrol.transports.telnetlib as telnetlib
sys.path.insert(0, os.path.dirname(sys.argv[0]) + "/pyssh")    
import pcucontrol.transports.pyssh as pyssh
from monitor import config


# Event class ID from pcu events
#NODE_POWER_CONTROL = 3

# Monitor user ID
#MONITOR_USER_ID = 11142

import logging
logger = logging.getLogger("monitor")
verbose = 1
#dryrun = 0;

class ExceptionNoTransport(Exception): pass
class ExceptionNotFound(Exception): pass
class ExceptionPassword(Exception): pass
class ExceptionTimeout(Exception): pass
class ExceptionPrompt(Exception): pass
class ExceptionSequence(Exception): pass
class ExceptionReset(Exception): pass
class ExceptionPort(Exception): pass
class ExceptionUsername(Exception): pass



# PCU has model, host, preferred-port, user, passwd, 

# This is an object derived directly form the PLCAPI DB fields
class PCU(object):
	def __init__(self, plc_pcu_dict):
		for field in ['username', 'password', 'site_id', 
						'hostname', 'ip', 
						'pcu_id', 'model', 
						'node_ids', 'ports', ]:
			if field in plc_pcu_dict:
				self.__setattr__(field, plc_pcu_dict[field])
			else:
				raise Exception("No such field %s in PCU object" % field)

# These are the convenience functions build around the PCU object.
class PCUModel(PCU):
	def __init__(self, plc_pcu_dict):
		PCU.__init__(self, plc_pcu_dict)
		self.host = self.pcu_name()

	def pcu_name(self):
		if self.hostname is not None and self.hostname is not "":
			return self.hostname
		elif self.ip is not None and self.ip is not "":
			return self.ip
		else:
			return None

	def nodeidToPort(self, node_id):
		if node_id in self.node_ids:
			for i in range(0, len(self.node_ids)):
				if node_id == self.node_ids[i]:
					return self.ports[i]

		raise Exception("No such Node ID: %d" % node_id)

# This class captures the observed pcu records from FindBadPCUs.py
class PCURecord:
	def __init__(self, pcu_record_dict):
		for field in ['port_status', 
						'dns_status', 
						'entry_complete', ]:
			if field in pcu_record_dict:
				if field == "reboot":
					self.__setattr__("reboot_str", pcu_record_dict[field])
				else:
					self.__setattr__(field, pcu_record_dict[field])
			#else:
			#	raise Exception("No such field %s in pcu record dict" % field)

class Transport:
	TELNET = "telnet"
	SSH    = "ssh"
	HTTP   = "http"
	HTTPS  = "https"
	IPAL   = "ipal"
	DRAC   = "drac"
	AMT    = "amt"

	TELNET_TIMEOUT = 120

	porttypemap = {
			5869 : DRAC,
			22 : SSH,
			23 : TELNET,
			443 : HTTPS,
			80 :  HTTP,
			9100 : IPAL,
			16992 : AMT,
		}

	def __init__(self, type, verbose):
		self.type = type
		self.verbose = verbose
		self.transport = None

	def open(self, host, username=None, password=None, prompt="User Name"):
		transport = None

		if self.type == self.TELNET:
			transport = telnetlib.Telnet(host, timeout=self.TELNET_TIMEOUT)
			transport.set_debuglevel(self.verbose)
			if username is not None:
				self.transport = transport
				self.transport.ifThenSend(prompt, username, ExceptionUsername)

		elif self.type == self.SSH:
			if username is not None:
				transport = pyssh.Ssh(username, host)
				transport.set_debuglevel(self.verbose)
				transport.open()
				# TODO: have an ssh set_debuglevel() also...
			else:
				raise Exception("Username cannot be None for ssh transport.")
		elif self.type == self.HTTP:
			# NOTE: this does not work for all web-based services...
			self.url = "http://%s:%d/" % (host,80)
			uri = "%s:%d" % (host,80)

			# create authinfo
			authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
			authinfo.add_password (None, uri, username, password)
			authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

			transport = urllib2.build_opener(authhandler)
		else:
			raise Exception("Unknown transport type: %s" % self.type)

		self.transport = transport
		return True

	def close(self):
		if self.type == self.TELNET:
			self.transport.close() 
		elif self.type == self.SSH:
			self.transport.close() 
		elif self.type == self.HTTP:
			pass
		else:
			raise Exception("Unknown transport type %s" % self.type)
		self.transport = None

	def write(self, msg):
		return self.send(msg)

	def send(self, msg):
		if self.transport == None:
			raise ExceptionNoTransport("transport object is type None")
			
		return self.transport.write(msg)

	def sendPassword(self, password, prompt=None):
		if self.type == self.TELNET:
			if prompt == None:
				self.ifThenSend("Password", password, ExceptionPassword)
			else:
				self.ifThenSend(prompt, password, ExceptionPassword)
		elif self.type == self.SSH:
			self.ifThenSend("password:", password, ExceptionPassword)
		elif self.type == self.HTTP:
			pass
		else:
			raise Exception("Unknown transport type: %s" % self.type)

	def sendHTTP(self, resource, data):
		if self.verbose:
			print "POSTing '%s' to %s" % (data,self.url + resource)

		try:
			f = self.transport.open(self.url + resource ,data)
			r = f.read()
			if self.verbose:
				print r

		except urllib2.URLError,err:
			logger.info('Could not open http connection', err)
			return "http transport error"

		return 0

	def ifThenSend(self, expected, buffer, ErrorClass=ExceptionPrompt):

		if self.transport != None:
			output = self.transport.read_until(expected, self.TELNET_TIMEOUT)
			if output.find(expected) == -1:
				print "OUTPUT: --%s--" % output
				raise ErrorClass, "'%s' not found" % expected
			else:
				self.transport.write(buffer + "\r\n")
		else:
			raise ExceptionNoTransport("transport object is type None")

	def ifElse(self, expected, ErrorClass):
		try:
			self.transport.read_until(expected, self.TELNET_TIMEOUT)
		except:
			raise ErrorClass("Could not find '%s' within timeout" % expected)

class PCUControl(PCUModel,PCURecord):

	""" 
		There are three cases:
			1) the pcu_record passed below includes port_status from an
				external probe.
			2) the external probe failed, and the values are empty
			3) this call is made independent of port_status.

		In the first case, the first open port is used.
		In the third case, the ports are tried in sequence.

		In this way, the port_status value serves only as an optimization,
		because closed ports are avoided.  The supported_ports value should
		order ports by their preferred usage.
	"""

	supported_ports = []

	def __init__(self, plc_pcu_record, verbose, ignored=None):
		PCUModel.__init__(self, plc_pcu_record)
		PCURecord.__init__(self, plc_pcu_record)

	def reboot(self, node_port, dryrun):

		port_list = []
		if hasattr(self, 'port_status') and self.port_status:
			port_list = filter(lambda x: self.port_status[x] == "open" , self.port_status.keys())
			port_list = [ int(x) for x in port_list ]
			if port_list == []:
				raise ExceptionPort("Unsupported Port: No transport from open ports")
		else:
			port_list = self.supported_ports

		print port_list

		ret = "could not run"
		for port in port_list:
			if port not in Transport.porttypemap:
				continue

			type = Transport.porttypemap[port]
			self.transport = Transport(type, verbose)

			if hasattr(self, "run_%s" % type):
				fxn = getattr(self, "run_%s" % type)
				ret = self.catcherror(fxn, node_port, dryrun)
				if ret == 0: # NOTE: success!, so stop
					break
			else:
				continue

		return ret

	def run(self, node_port, dryrun):
		""" This function is to be defined by the specific PCU instance.  """
		raise Exception("This function is not implemented")
		pass

	#def reboot(self, node_port, dryrun):

	def catcherror(self, function, node_port, dryrun):
		try:
			return function(node_port, dryrun)
		except ExceptionNotFound, err:
			return "error: " + str(err)
		except ExceptionPassword, err:
			return "Password exception: " + str(err)
		except ExceptionTimeout, err:
			return "Timeout exception: " + str(err)
		except ExceptionUsername, err:
			return "No username prompt: " + str(err)
		except ExceptionSequence, err:
			return "Sequence error: " + str(err)
		except ExceptionPrompt, err:
			return "Prompt exception: " + str(err)
		except ExceptionNoTransport, err:
			return "No Transport: " + str(err)
		except ExceptionPort, err:
			return "No ports exception: " + str(err)
		except socket.error, err:
			return "socket error: timeout: " + str(err)
		except urllib2.HTTPError, err:
			return "HTTPError: " + str(err)
		except urllib2.URLError, err:
			return "URLError: " + str(err)
		except EOFError, err:
			if self.verbose:
				logger.debug("reboot: EOF")
				logger.debug(err)
			self.transport.close()
			import traceback
			traceback.print_exc()
			return "EOF connection reset" + str(err)

from pcucontrol.models import *

def pcu_name(pcu):
	if pcu['hostname'] is not None and pcu['hostname'] is not "":
		return pcu['hostname']
	elif pcu['ip'] is not None and pcu['ip'] is not "":
		return pcu['ip']
	else:
		return None

def get_pcu_values(pcu_id):
	from monitor.database.info.model import FindbadPCURecord
	print "pcuid: %s" % pcu_id
	try:
		pcurec = FindbadPCURecord.get_latest_by(plc_pcuid=pcu_id).first()
		if pcurec:
			values = pcurec.to_dict()
		else:
			values = None
	except:
		values = None

	return values

def reboot(nodename):
	return reboot_policy(nodename, True, False)

def reboot_str(nodename):
	global verbose
	continue_probe = True
	dryrun=False

	pcu = plc.getpcu(nodename)
	if not pcu:
		logger.debug("no pcu for %s" % nodename)
		print "no pcu for %s" % nodename
		return False # "%s has no pcu" % nodename

	values = get_pcu_values(pcu['pcu_id'])
	if values == None:
		logger.debug("No values for pcu probe %s" % nodename)
		print "No values for pcu probe %s" % nodename
		return False #"no info for pcu_id %s" % pcu['pcu_id']
	
	# Try the PCU first
	logger.debug("Trying PCU %s %s" % (pcu['hostname'], pcu['model']))

	ret = reboot_test_new(nodename, values, verbose, dryrun)
	return ret
	
def reboot_policy(nodename, continue_probe, dryrun):
	global verbose

	pcu = plc.getpcu(nodename)
	if not pcu:
		logger.debug("no pcu for %s" % nodename)
		print "no pcu for %s" % nodename
		return False # "%s has no pcu" % nodename

	values = get_pcu_values(pcu['pcu_id'])
	if values == None:
		logger.debug("No values for pcu probe %s" % nodename)
		print "No values for pcu probe %s" % nodename
		return False #"no info for pcu_id %s" % pcu['pcu_id']
	
	# Try the PCU first
	logger.debug("Trying PCU %s %s" % (pcu['hostname'], pcu['model']))

	ret = reboot_test_new(nodename, values, verbose, dryrun)

	if ret != 0:
		print ret
		return False
	else:
		print "return true"
		return True

class Unknown(PCUControl):
	supported_ports = [22,23,80,443,5869,9100,16992]

def model_to_object(modelname):
	if modelname is None:
		return ManualPCU 
	if "AMT" in modelname:
		return IntelAMT
	elif "BayTech" in modelname:
		return BayTech
	elif "HPiLO" in modelname:
		return HPiLO
	elif "IPAL" in modelname:
		return IPAL
	elif "APC" in modelname:
		return APCControl
	elif "DRAC" in modelname:
		return DRAC
	elif "WTI" in modelname:
		return WTIIPS4
	elif "ePowerSwitch" in modelname:
		return ePowerSwitchNew
	elif "IPMI" in modelname:
		return IPMI
	elif "BlackBoxPSMaverick" in modelname:
		return BlackBoxPSMaverick
	elif "PM211MIP" in modelname:
		return PM211MIP
	elif "ManualPCU" in modelname:
		return ManualPCU 
	else:
		print "UNKNOWN model %s"%modelname
		return Unknown

def reboot_api(node, pcu): #, verbose, dryrun):
	rb_ret = ""

	try:
		modelname = pcu['model']
		if modelname:
			# get object instance 
			instance = eval('%s(pcu, verbose)' % modelname)
			# get pcu port 
			i = pcu['node_ids'].index(node['node_id'])
			p = pcu['ports'][i]
			# reboot
			rb_ret = instance.reboot(p, False)
		else:
			rb_ret =  "No modelname in PCU record."
		# TODO: how to handle the weird, georgetown pcus, the drac faults, and ilo faults
	except Exception, err:
		rb_ret = str(err)

	return rb_ret

def reboot_test_new(nodename, values, verbose, dryrun):
	rb_ret = ""
	if 'plc_pcu_stats' in values:
		values.update(values['plc_pcu_stats'])

	try:
		modelname = values['model']
		if modelname:
			object = eval('%s(values, verbose, ["22", "23", "80", "443", "9100", "16992", "5869"])' % modelname)
			rb_ret = object.reboot(values[nodename], dryrun)
		else:
			rb_ret =  "Not_Run"
		# TODO: how to handle the weird, georgetown pcus, the drac faults, and ilo faults
	except ExceptionPort, err:
		rb_ret = str(err)
	except NameError, err:
		rb_ret = str(err)

	return rb_ret

def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('LOGGER - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	try:
		if "test" in sys.argv:
			dryrun = True
		else:
			dryrun = False

		for node in sys.argv[1:]:
			if node == "test": continue

			print "Rebooting %s" % node
			if reboot_policy(node, True, dryrun):
				print "success"
			else:
				print "failed"
	except Exception, err:
		import traceback; traceback.print_exc()
		print err

if __name__ == '__main__':
	logger = logging.getLogger("monitor")
	main()
	f = open("/tmp/rebootlog", 'a')
	f.write("reboot %s\n" % sys.argv)
	f.close()
