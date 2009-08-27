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
import base64
from subprocess import PIPE, Popen
import pcucontrol.transports.ssh.pxssh as pxssh
import pcucontrol.transports.ssh.pexpect as pexpect
import socket



# Use our versions of telnetlib and pyssh
sys.path.insert(0, os.path.dirname(sys.argv[0]))
import pcucontrol.transports.telnetlib as telnetlib
sys.path.insert(0, os.path.dirname(sys.argv[0]) + "/pyssh")    
import pcucontrol.transports.pyssh as pyssh

# Event class ID from pcu events
#NODE_POWER_CONTROL = 3

# Monitor user ID
#MONITOR_USER_ID = 11142

import logging
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
				if type(u"") == type(plc_pcu_dict[field]):
					# NOTE: if is a unicode string, convert it.
					self.__setattr__(field, str(plc_pcu_dict[field]))
				else:
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
				self.ifThenSend(prompt, username, ExceptionUsername)

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
			print 'Could not open http connection', err
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
		# There are two sources of potential ports.  Those that are open and
		# those that are part of the PCU's supported_ports.  
		#  I think we should start with supported_ports and then filter that
		#  by the open ports.

		port_list = self.supported_ports

		if hasattr(self, 'port_status') and self.port_status:
			# get out the open ports
			port_list = filter(lambda x: self.port_status[x] == "open" , self.port_status.keys())
			port_list = [ int(x) for x in port_list ]
			# take only the open ports that are supported_ports
			port_list = filter(lambda x: x in self.supported_ports, port_list)
			if port_list == []:
				raise ExceptionPort("No Open Port: No transport from open ports")

		print port_list

		ret = "No implementation for open ports on selected PCU model"
		for port in port_list:
			if port not in Transport.porttypemap:
				continue

			type = Transport.porttypemap[port]
			self.transport = Transport(type, verbose)

			print "checking for run_%s" % type
			if hasattr(self, "run_%s" % type):
				print "found run_%s" % type
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
			self.transport.close()
			import traceback
			traceback.print_exc()
			return "EOF connection reset" + str(err)
		except Exception, err:
			#from monitor.common import email_exception
			#email_exception(self.host)
			raise Exception(err)

from pcucontrol.util import command
from pcucontrol.models import *

def pcu_name(pcu):
	if pcu['hostname'] is not None and pcu['hostname'] is not "":
		return pcu['hostname']
	elif pcu['ip'] is not None and pcu['ip'] is not "":
		return pcu['ip']
	else:
		return None

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
		return OpenIPMI
	elif "BlackBoxPSMaverick" in modelname:
		return BlackBoxPSMaverick
	elif "PM211MIP" in modelname:
		return PM211MIP
	elif "ManualPCU" in modelname:
		return ManualPCU 
	else:
		print "UNKNOWN model %s"%modelname
		return Unknown

def reboot_api(node, pcu):
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
		rb_ret = "Exception Model(%s): " % modelname 
		rb_ret += str(err)

	return rb_ret

def convert_oldmodelname_to_newmodelname(oldmodelname, pcu_id):
	newmodelname = None
	update = {	'AP79xx' : 'APCControl13p13',
				'Masterswitch' : 'APCControl13p13',
				'DS4-RPC' : 'BayTech',
				'IP-41x_IP-81x' : 'IPAL',
				'DRAC3' : 'DRAC',
				'DRAC4' : 'DRAC',
				'ePowerSwitch' : 'ePowerSwitchOld',
				'ilo2' : 'HPiLO',
				'ilo1' : 'HPiLO',
				'PM211-MIP' : 'PM211MIP',
				'AMT2.5' : 'IntelAMT',
				'AMT3.0' : 'IntelAMT',
				'WTI_IPS-4' : 'WTIIPS4',
				'unknown'  : 'ManualPCU',
				'DRAC5'	: 'DRAC',
				'ipmi'	: 'OpenIPMI',
				'bbsemaverick' : 'BlackBoxPSMaverick',
				'manualadmin'  : 'ManualPCU',
	}

	if oldmodelname in update:
		newmodelname = update[oldmodelname]
	else:
		newmodelname = oldmodelname

	if pcu_id in [1102,1163,1055,1111,1231,1113,1127,1128,1148]:
		newmodelname = 'APCControl12p3'
	elif pcu_id in [1110,86]:
		newmodelname = 'APCControl1p4'
	elif pcu_id in [1221,1225,1220,1192]:
		newmodelname = 'APCControl121p3'
	elif pcu_id in [1173,1240,47,1363,1405,1401,1372,1371]:
		newmodelname = 'APCControl121p1'
	elif pcu_id in [1056,1237,1052,1209,1002,1008,1013,1022]:
		newmodelname = 'BayTechCtrlC'
	elif pcu_id in [93]:
		newmodelname = 'BayTechRPC3NC'
	elif pcu_id in [1057]:
		newmodelname = 'BayTechCtrlCUnibe'
	elif pcu_id in [1012]:
		newmodelname = 'BayTechRPC16'
	elif pcu_id in [1089, 1071, 1046, 1035, 1118]:
		newmodelname = 'ePowerSwitchNew'

	return newmodelname

def reboot_test_new(nodename, values, verbose, dryrun):
	rb_ret = ""
	if 'plc_pcu_stats' in values:
		values.update(values['plc_pcu_stats'])

	try:
		#modelname = convert_oldmodelname_to_newmodelname(values['model'], values['pcu_id'])
		modelname = values['model']
		if modelname:
			object = eval('%s(values, verbose)' % modelname)
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
	print "this does not work."

if __name__ == '__main__':
	main()
