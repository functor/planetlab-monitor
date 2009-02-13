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
import plc
import base64
from subprocess import PIPE, Popen
import ssh.pxssh as pxssh
import ssh.pexpect as pexpect
import socket
import moncommands 

# Use our versions of telnetlib and pyssh
sys.path.insert(0, os.path.dirname(sys.argv[0]))
import telnetlib
sys.path.insert(0, os.path.dirname(sys.argv[0]) + "/pyssh")    
import pyssh

# Timeouts in seconds
TELNET_TIMEOUT = 45

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
		for field in ['nodenames', 'portstatus', 
						'dnsmatch', 
						'complete_entry', ]:
			if field in pcu_record_dict:
				if field == "reboot":
					self.__setattr__("reboot_str", pcu_record_dict[field])
				else:
					self.__setattr__(field, pcu_record_dict[field])
			else:
				raise Exception("No such field %s in pcu record dict" % field)

class Transport:
	TELNET = 1
	SSH    = 2
	HTTP   = 3
	IPAL   = 4

	TELNET_TIMEOUT = 60

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

	def ifThenSend(self, expected, buffer, ErrorClass=ExceptionPrompt):

		if self.transport != None:
			output = self.transport.read_until(expected, self.TELNET_TIMEOUT)
			if output.find(expected) == -1:
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
			

class PCUControl(Transport,PCUModel,PCURecord):
	def __init__(self, plc_pcu_record, verbose, supported_ports=[]):
		PCUModel.__init__(self, plc_pcu_record)
		PCURecord.__init__(self, plc_pcu_record)
		type = None
		if self.portstatus:
			if '22' in supported_ports and self.portstatus['22'] == "open":
				type = Transport.SSH
			elif '23' in supported_ports and self.portstatus['23'] == "open":
				type = Transport.TELNET
			elif '80' in supported_ports and self.portstatus['80'] == "open":
				type = Transport.HTTP
			elif '443' in supported_ports and self.portstatus['443'] == "open":
				type = Transport.HTTP
			elif '5869' in supported_ports and self.portstatus['5869'] == "open":
				# For DRAC cards. Racadm opens this port.
				type = Transport.HTTP
			elif '9100' in supported_ports and self.portstatus['9100'] == "open":
				type = Transport.IPAL
			elif '16992' in supported_ports and self.portstatus['16992'] == "open":
				type = Transport.HTTP
			else:
				raise ExceptionPort("Unsupported Port: No transport from open ports")
		else:
			raise Exception("No Portstatus: No transport because no open ports")
		Transport.__init__(self, type, verbose)

	def run(self, node_port, dryrun):
		""" This function is to be defined by the specific PCU instance.  """
		pass
		
	def reboot(self, node_port, dryrun):
		try:
			return self.run(node_port, dryrun)
		except ExceptionNotFound, err:
			return "error: " + str(err)
		except ExceptionPassword, err:
			return "password exception: " + str(err)
		except ExceptionTimeout, err:
			return "timeout exception: " + str(err)
		except ExceptionUsername, err:
			return "exception: no username prompt: " + str(err)
		except ExceptionSequence, err:
			return "sequence error: " + str(err)
		except ExceptionPrompt, err:
			return "prompt exception: " + str(err)
		except ExceptionPort, err:
			return "no ports exception: " + str(err)
		except socket.error, err:
			return "socket error: timeout: " + str(err)
		except EOFError, err:
			if self.verbose:
				logger.debug("reboot: EOF")
				logger.debug(err)
			self.transport.close()
			import traceback
			traceback.print_exc()
			return "EOF connection reset" + str(err)
		
class IPAL(PCUControl):
	""" 
		This now uses a proprietary format for communicating with the PCU.  I
		prefer it to Telnet, and Web access, since it's much lighter weight
		and, more importantly, IT WORKS!! HHAHHHAHAHAHAHAHA!
	"""

	def format_msg(self, data, cmd):
		esc = chr(int('1b',16))
		return "%c%s%c%s%c" % (esc, self.password, esc, data, cmd) # esc, 'q', chr(4))
	
	def recv_noblock(self, s, count):
		import errno

		try:
			# TODO: make sleep backoff, before stopping.
			time.sleep(4)
			ret = s.recv(count, socket.MSG_DONTWAIT)
		except socket.error, e:
			if e[0] == errno.EAGAIN:
				raise Exception(e[1])
			else:
				# TODO: not other exceptions.
				raise Exception(e)
		return ret

	def run(self, node_port, dryrun):
		import errno

		power_on = False

		print "open socket"
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			print "connect"
			s.connect((self.host, 9100))
		except socket.error, e:
			s.close()
			if e[0] == errno.ECONNREFUSED:
				# cannot connect to remote host
				raise Exception(e[1])
			else:
				# TODO: what other conditions are there?
				raise Exception(e)
				
		# get current status
		print "Checking status"
		s.send(self.format_msg("", 'O'))
		ret = self.recv_noblock(s, 8)
		print "Current status is '%s'" % ret

		if ret == '':
			raise Exception("Status returned 'another session already open' %s : %s" % (node_port, ret))
			
				
		if node_port < len(ret):
			status = ret[node_port]
			if status == '1':
				# up
				power_on = True
			elif status == '0':
				# down
				power_on = False
			else:
				raise Exception("Unknown status for PCU socket %s : %s" % (node_port, ret))
		else:
			raise Exception("Mismatch between configured port and PCU status: %s %s" % (node_port, ret))
			

		if not dryrun:
			if power_on:
				print "Pulsing %s" % node_port
				s.send(self.format_msg("%s" % node_port, 'P'))
			else:
				# NOTE: turn power on ; do not pulse the port.
				print "Power was off, so turning on ..."
				s.send(self.format_msg("%s" % node_port, 'E'))
				#s.send(self.format_msg("%s" % node_port, 'P'))

			print "Receiving response."
			ret = self.recv_noblock(s, 8)
			print "Current status is '%s'" % ret

			if node_port < len(ret):
				status = ret[node_port]
				if status == '1':
					# up
					power_on = True
				elif status == '0':
					# down
					power_on = False
				else:
					raise Exception("Unknown status for PCU socket %s : %s" % (node_port, ret))
			else:
				raise Exception("Mismatch between configured port and PCU status: %s %s" % (node_port, ret))

			if power_on:
				return 0
			else:
				return "Failed Power On"

		s.close()
		return 0

# TELNET version of protocol...
#		#self.open(self.host)
#		## XXX Some iPals require you to hit Enter a few times first
#		#self.ifThenSend("Password >", "\r\n\r\n", ExceptionNotFound)
#		# Login
#		self.ifThenSend("Password >", self.password, ExceptionPassword)
#		self.transport.write("\r\n\r\n")
#		if not dryrun: # P# - Pulse relay
#			print "node_port %s" % node_port
#			self.ifThenSend("Enter >", 
#							"P7", # % node_port, 
#							ExceptionNotFound)
#			print "send newlines"
#			self.transport.write("\r\n\r\n")
#			print "after new lines"
#		# Get the next prompt
#		print "wait for enter"
#		self.ifElse("Enter >", ExceptionTimeout)
#		print "closing "
#		self.close()
#		return 0

class APCEurope(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		self.ifThenSend("\r\n> ", "1", ExceptionPassword)
		self.ifThenSend("\r\n> ", "2")
		self.ifThenSend("\r\n> ", str(node_port))
		# 3- Immediate Reboot		  
		self.ifThenSend("\r\n> ", "3")

		if not dryrun:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.close()
		return 0

class APCBrazil(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		self.ifThenSend("\r\n> ", "1", ExceptionPassword)
		self.ifThenSend("\r\n> ", str(node_port))
		# 4- Immediate Reboot		  
		self.ifThenSend("\r\n> ", "4")

		if not dryrun:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.close()
		return 0

class APCBerlin(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		self.ifThenSend("\r\n> ", "1", ExceptionPassword)
		self.ifThenSend("\r\n> ", "2")
		self.ifThenSend("\r\n> ", "1")
		self.ifThenSend("\r\n> ", str(node_port))
		# 3- Immediate Reboot		  
		self.ifThenSend("\r\n> ", "3")

		if not dryrun:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.close()
		return 0

class APCFolsom(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		self.ifThenSend("\r\n> ", "1", ExceptionPassword)
		self.ifThenSend("\r\n> ", "2")
		self.ifThenSend("\r\n> ", "1")
		self.ifThenSend("\r\n> ", str(node_port))
		self.ifThenSend("\r\n> ", "1")

		# 3- Immediate Reboot		  
		self.ifThenSend("\r\n> ", "3")

		if not dryrun:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.close()
		return 0

class APCMaster(PCUControl):
	def run(self, node_port, dryrun):
		print "Rebooting %s" % self.host
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		# 1- Device Manager
		self.ifThenSend("\r\n> ", "1", ExceptionPassword)
		# 3- Outlet Control/Config
		self.ifThenSend("\r\n> ", "3")
		# n- Outlet n
		self.ifThenSend("\r\n> ", str(node_port))
		# 1- Control Outlet
		self.ifThenSend("\r\n> ", "1")
		# 3- Immediate Reboot		  
		self.ifThenSend("\r\n> ", "3")

		if not dryrun:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.close()
		return 0

class APC(PCUControl):
	def __init__(self, plc_pcu_record, verbose):
		PCUControl.__init__(self, plc_pcu_record, verbose)

		self.master = APCMaster(plc_pcu_record, verbose)
		self.folsom = APCFolsom(plc_pcu_record, verbose)
		self.europe = APCEurope(plc_pcu_record, verbose)

	def run(self, node_port, dryrun):
		try_again = True
		sleep_time = 1

		for pcu in [self.master, self.europe, self.folsom]:
			if try_again:
				try:
					print "-*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*_*"
					try_again = False
					print "sleeping 5"
					time.sleep(sleep_time)
					ret = pcu.reboot(node_port, dryrun)
				except ExceptionSequence, err:
					del pcu
					sleep_time = 130
					try_again = True

		if try_again:
			return "Unknown reboot sequence for APC PCU"
		else:
			return ret

class IntelAMT(PCUControl):
	def run(self, node_port, dryrun):

		cmd = moncommands.CMD()
		#[cmd_str = "IntelAMTSDK/Samples/RemoteControl/remoteControl"
		cmd_str = "cmdamt/remoteControl"

		if dryrun:
			# NOTE: -p checks the power state of the host.
			# TODO: parse the output to find out if it's ok or not.
			cmd_str += " -p http://%s:16992/RemoteControlService  -user admin -pass '%s' " % (self.host, self.password )
		else:
			cmd_str += " -A http://%s:16992/RemoteControlService -user admin -pass '%s' " % (self.host, self.password )
			
		print cmd_str
		return cmd.system(cmd_str, self.TELNET_TIMEOUT)

class DRACRacAdm(PCUControl):
	def run(self, node_port, dryrun):

		print "trying racadm_reboot..."
		racadm_reboot(self.host, self.username, self.password, node_port, dryrun)

		return 0

class DRAC(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		print "logging in..."
		self.transport.write("\r\n")
		# Testing Reboot ?
		if dryrun:
			self.ifThenSend("[%s]#" % self.username, "getsysinfo")
		else:
			# Reset this machine
			self.ifThenSend("[%s]#" % self.username, "serveraction powercycle")

		self.ifThenSend("[%s]#" % self.username, "exit")

		self.close()
		return 0

class HPiLO(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		# </>hpiLO-> 
		self.ifThenSend("</>hpiLO->", "cd system1")

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.ifThenSend("</system1>hpiLO->", "POWER")
		else:
			# Reset this machine
			self.ifThenSend("</system1>hpiLO->", "reset")

		self.ifThenSend("</system1>hpiLO->", "exit")

		self.close()
		return 0

		
class HPiLOHttps(PCUControl):
	def run(self, node_port, dryrun):

		locfg = moncommands.CMD()
		cmd = "cmdhttps/locfg.pl -s %s -f %s -u %s -p '%s' | grep 'MESSAGE' | grep -v 'No error'" % (
					self.host, "iloxml/Get_Network.xml", 
					self.username, self.password)
		sout, serr = locfg.run_noexcept(cmd)

		if sout.strip() != "":
			print "sout: %s" % sout.strip()
			return sout.strip()

		if not dryrun:
			locfg = moncommands.CMD()
			cmd = "cmdhttps/locfg.pl -s %s -f %s -u %s -p '%s' | grep 'MESSAGE' | grep -v 'No error'" % (
						self.host, "iloxml/Reset_Server.xml", 
						self.username, self.password)
			sout, serr = locfg.run_noexcept(cmd)

			if sout.strip() != "":
				print "sout: %s" % sout.strip()
				#return sout.strip()
		return 0

class BayTechAU(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username, None, "Enter user name:")
		self.sendPassword(self.password, "Enter Password:")

		#self.ifThenSend("RPC-16>", "Status")
		self.ifThenSend("RPC3-NC>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.ifThenSend("(Y/N)?", "N")
		else:
			self.ifThenSend("(Y/N)?", "Y")
		self.ifThenSend("RPC3-NC>", "")

		self.close()
		return 0

class BayTechGeorgeTown(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username, None, "Enter user name:")
		self.sendPassword(self.password, "Enter Password:")

		#self.ifThenSend("RPC-16>", "Status")

		self.ifThenSend("RPC-16>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.ifThenSend("(Y/N)?", "N")
		else:
			self.ifThenSend("(Y/N)?", "Y")
		self.ifThenSend("RPC-16>", "")

		self.close()
		return 0

class BayTechCtrlCUnibe(PCUControl):
	"""
		For some reason, these units let you log in fine, but they hang
		indefinitely, unless you send a Ctrl-C after the password.  No idea
		why.
	"""
	def run(self, node_port, dryrun):
		print "BayTechCtrlC %s" % self.host

		ssh_options="-o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		if not s.login(self.host, self.username, self.password, ssh_options):
			raise ExceptionPassword("Invalid Password")
		# Otherwise, the login succeeded.

		# Send a ctrl-c to the remote process.
		print "sending ctrl-c"
		s.send(chr(3))

		# Control Outlets  (5 ,1).........5
		try:
			#index = s.expect("Enter Request")
			index = s.expect(["Enter Request :"])

			if index == 0:
				print "3"
				s.send("3\r\n")
				index = s.expect(["DS-RPC>", "Enter user name:"])
				if index == 1:
					s.send(self.username + "\r\n")
					index = s.expect(["DS-RPC>"])

				if index == 0:
					print "Reboot %d" % node_port
					s.send("Reboot %d\r\n" % node_port)

					time.sleep(5)
					index = s.expect(["\(Y/N\)\?", "Port in use", "DS-RPC>"])
					if index == 0:
						if dryrun:
							print "sending N"
							s.send("N\r\n")
						else:
							print "sending Y"
							s.send("Y\r\n")
					elif index == 1:
						raise ExceptionPrompt("PCU Reported 'Port in use.'")
					elif index == 2:
						raise ExceptionSequence("Issued command 'Reboot' failed.")

				time.sleep(5)
				index = s.expect(["DS-RPC>"])
				#print "got prompt back"

			s.close()

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before expected Prompt")
		except pexpect.TIMEOUT:
			raise ExceptionPrompt("Timeout before expected Prompt")

		return 0

class BayTechCtrlC(PCUControl):
	"""
		For some reason, these units let you log in fine, but they hang
		indefinitely, unless you send a Ctrl-C after the password.  No idea
		why.
	"""
	def run(self, node_port, dryrun):
		print "BayTechCtrlC %s" % self.host

		ssh_options="-o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		if not s.login(self.host, self.username, self.password, ssh_options):
			raise ExceptionPassword("Invalid Password")
		# Otherwise, the login succeeded.

		# Send a ctrl-c to the remote process.
		print "SENDING ctrl-c"
		s.send(chr(3))

		# Control Outlets  (5 ,1).........5
		try:
			print "EXPECTING: ", "Enter Request :"
			index = s.expect(["Enter Request :"])

			if index == 0:
				print "SENDING: 5"
				s.send("5\r\n")
				print "EXPECTING: ", "DS-RPC>"
				index = s.expect(["DS-RPC>", "Enter user name:", "Port in use."])
				if index == 1:
					print "sending username"
					s.send(self.username + "\r\n")
					index = s.expect(["DS-RPC>"])
				elif index == 2:
					raise ExceptionPrompt("PCU Reported 'Port in use.'")

				if index == 0:
					print "SENDING: Reboot %d" % node_port
					s.send("Reboot %d\r\n" % node_port)

					print "SLEEPING: 5"
					time.sleep(5)
					print "EXPECTING: ", "Y/N?"
					index = s.expect(["\(Y/N\)\?", "Port in use", "DS-RPC>"])
					if index == 0:
						if dryrun:
							print "sending N"
							s.send("N\r\n")
						else:
							print "SENDING: Y"
							s.send("Y\r\n")
					elif index == 1:
						raise ExceptionPrompt("PCU Reported 'Port in use.'")
					elif index == 2:
						raise ExceptionSequence("Issued command 'Reboot' failed.")

				# NOTE: for some reason, the script times out with the
				# following line.  In manual tests, it works correctly, but
				# with automated tests, evidently it fails.
				print "SLEEPING: 5"
				time.sleep(5)
				#print "TOTAL--", s.allstr, "--EOT"
				index = s.expect(["DS-RPC>"])
				print "got prompt back"

			s.close()

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before 'Enter Request' Prompt")
		except pexpect.TIMEOUT:
			raise ExceptionPrompt("Timeout before Prompt")

		return 0

class BayTech(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host, self.username)
		self.sendPassword(self.password)

		# Control Outlets  (5 ,1).........5
		self.ifThenSend("Enter Request :", "5")

		# Reboot N
		try:
			self.ifThenSend("DS-RPC>", "Reboot %d" % node_port, ExceptionNotFound)
		except ExceptionNotFound, msg:
			# one machine is configured to ask for a username,
			# even after login...
			print "msg: %s" % msg
			self.transport.write(self.username + "\r\n")
			time.sleep(5)
			self.ifThenSend("DS-RPC>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.ifThenSend("(Y/N)?", "N")
		else:
			self.ifThenSend("(Y/N)?", "Y")
		time.sleep(5)
		self.ifThenSend("DS-RPC>", "")

		self.close()
		return 0

class WTIIPS4(PCUControl):
	def run(self, node_port, dryrun):
		self.open(self.host)
		self.sendPassword(self.password, "Enter Password:")

		self.ifThenSend("IPS> ", "/Boot %s" % node_port)
		if not dryrun:
			self.ifThenSend("Sure? (Y/N): ", "N")
		else:
			self.ifThenSend("Sure? (Y/N): ", "Y")

		self.ifThenSend("IPS> ", "")

		self.close()
		return 0

class ePowerSwitchGood(PCUControl):
	# NOTE:
	# 		The old code used Python's HTTPPasswordMgrWithDefaultRealm()
	#		For some reason this both doesn't work and in some cases, actually
	#		hangs the PCU.  Definitely not what we want.
	#		
	# 		The code below is much simpler.  Just letting things fail first,
	# 		and then, trying again with authentication string in the header.
	#		
	def run(self, node_port, dryrun):
		self.transport = None
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		req = urllib2.Request(self.url)
		try:
			handle = urllib2.urlopen(req)
		except IOError, e:
			# NOTE: this is expected to fail initially
			pass
		else:
			print self.url
			print "-----------"
			print handle.read()
			print "-----------"
			return "ERROR: not protected by HTTP authentication"

		if not hasattr(e, 'code') or e.code != 401:
			return "ERROR: failed for: %s" % str(e)

		base64data = base64.encodestring("%s:%s" % (self.username, self.password))[:-1]
		# NOTE: assuming basic realm authentication.
		authheader = "Basic %s" % base64data
		req.add_header("Authorization", authheader)

		try:
			f = urllib2.urlopen(req)
		except IOError, e:
			# failing here means the User/passwd is wrong (hopefully)
			raise ExceptionPassword("Incorrect username/password")

		# NOTE: after verifying that the user/password is correct, 
		# 		actually reboot the given node.
		if not dryrun:
			try:
				data = urllib.urlencode({'P%d' % node_port : "r"})
				req = urllib2.Request(self.url + "cmd.html")
				req.add_header("Authorization", authheader)
				# add data to handler,
				f = urllib2.urlopen(req, data)
				if self.verbose: print f.read()
			except:
				import traceback; traceback.print_exc()

				# fetch url one more time on cmd.html, econtrol.html or whatever.
				# pass
		else:
			if self.verbose: print f.read()

		self.close()
		return 0

class CustomPCU(PCUControl):
	def run(self, node_port, dryrun):
		url = "https://www-itec.uni-klu.ac.at/plab-pcu/index.php" 

		if not dryrun:
			# Turn host off, then on
			formstr = "plab%s=off" % node_port
			os.system("curl --user %s:%s --form '%s' --insecure %s" % (self.username, self.password, formstr, url))
			time.sleep(5)
			formstr = "plab%s=on" % node_port
			os.system("curl --user %s:%s --form '%s' --insecure %s" % (self.username, self.password, formstr, url))
		else:
			os.system("curl --user %s:%s --insecure %s" % (self.username, self.password, url))


class ePowerSwitchOld(PCUControl):
	def run(self, node_port, dryrun):
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		# create authinfo
		authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
		authinfo.add_password (None, uri, self.username, self.password)
		authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

		# NOTE: it doesn't seem to matter whether this authinfo is here or not.
		transport = urllib2.build_opener(authinfo)
		f = transport.open(self.url)
		if self.verbose: print f.read()

		if not dryrun:
			transport = urllib2.build_opener(authhandler)
			f = transport.open(self.url + "cmd.html", "P%d=r" % node_port)
			if self.verbose: print f.read()

		self.close()
		return 0

class ePowerSwitch(PCUControl):
	def run(self, node_port, dryrun):
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		# TODO: I'm still not sure what the deal is here.
		# 		two independent calls appear to need to be made before the
		# 		reboot will succeed.  It doesn't seem to be possible to do
		# 		this with a single call.  I have no idea why.

		# create authinfo
		authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
		authinfo.add_password (None, uri, self.username, self.password)
		authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

		# NOTE: it doesn't seem to matter whether this authinfo is here or not.
		transport = urllib2.build_opener()
		f = transport.open(self.url + "elogin.html", "pwd=%s" % self.password)
		if self.verbose: print f.read()

		if not dryrun:
			transport = urllib2.build_opener(authhandler)
			f = transport.open(self.url + "econtrol.html", "P%d=r" % node_port)
			if self.verbose: print f.read()

		#	data= "P%d=r" % node_port
		#self.open(self.host, self.username, self.password)
		#self.sendHTTP("elogin.html", "pwd=%s" % self.password)
		#self.sendHTTP("econtrol.html", data)
		#self.sendHTTP("cmd.html", data)

		self.close()
		return 0
		

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

def racadm_reboot(host, username, password, port, dryrun):
	global verbose

	ip = socket.gethostbyname(host)
	try:
		cmd = "/usr/sbin/racadm"
		os.stat(cmd)
		if not dryrun:
			output = runcmd(cmd, ["-r %s -i serveraction powercycle" % ip],
				username, password)
		else:
			output = runcmd(cmd, ["-r %s -i getsysinfo" % ip],
				username, password)

		print "RUNCMD: %s" % output
		if verbose:
			logger.debug(output)
		return 0

	except Exception, err:
		logger.debug("runcmd raised exception %s" % err)
		if verbose:
			logger.debug(err)
		return -1

def pcu_name(pcu):
	if pcu['hostname'] is not None and pcu['hostname'] is not "":
		return pcu['hostname']
	elif pcu['ip'] is not None and pcu['ip'] is not "":
		return pcu['ip']
	else:
		return None

#import database
from monitor import database
fb = None

def get_pcu_values(pcu_id):
	global fb
	if fb == None:
		# this shouldn't be loaded each time...
		fb = database.dbLoad("findbadpcus")
		
	try:
		values = fb['nodes']["id_%s" % pcu_id]['values']
	except:
		values = None

	return values

def reboot(nodename):
	return reboot_policy(nodename, True, False)
	
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

	ret = reboot_test(nodename, values, continue_probe, verbose, dryrun)

	if ret != 0:
		print ret
		return False
	else:
		print "return true"
		return True

def reboot_test(nodename, values, continue_probe, verbose, dryrun):
	rb_ret = ""

	try:
		# DataProbe iPal (many sites)
		if  continue_probe and values['model'].find("IP-41x_IP-81x") >= 0:
			ipal = IPAL(values, verbose, ['23', '80', '9100'])
			rb_ret = ipal.reboot(values[nodename], dryrun)
				
		# APC Masterswitch (Berkeley)
		elif continue_probe and ( values['model'].find("AP79xx") >= 0 or \
								  values['model'].find("Masterswitch") >= 0 ):
			print values

			# TODO: make a more robust version of APC
			if values['pcu_id'] in [1102,1163,1055,1111,1231,1113,1127,1128,1148]:
				apc = APCEurope(values, verbose, ['22', '23'])
				rb_ret = apc.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [1110,86]:
				apc = APCBrazil(values, verbose, ['22', '23'])
				rb_ret = apc.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [1221,1225,1220]:
				apc = APCBerlin(values, verbose, ['22', '23'])
				rb_ret = apc.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [1173,1240,47]:
				apc = APCFolsom(values, verbose, ['22', '23'])
				rb_ret = apc.reboot(values[nodename], dryrun)

			else:
				apc = APCMaster(values, verbose, ['22', '23'])
				rb_ret = apc.reboot(values[nodename], dryrun)

		# BayTech DS4-RPC
		elif continue_probe and values['model'].find("DS4-RPC") >= 0:
			if values['pcu_id'] in [1056,1237,1052,1209,1002,1008,1041,1013,1022]:
				# These  require a 'ctrl-c' to be sent... 
				baytech = BayTechCtrlC(values, verbose, ['22', '23'])
				rb_ret = baytech.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [93]:
				baytech = BayTechAU(values, verbose, ['22', '23'])
				rb_ret = baytech.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [1057]:
				# These  require a 'ctrl-c' to be sent... 
				baytech = BayTechCtrlCUnibe(values, verbose, ['22', '23'])
				rb_ret = baytech.reboot(values[nodename], dryrun)

			elif values['pcu_id'] in [1012]:
				# This pcu sometimes doesn't present the 'Username' prompt,
				# unless you immediately try again...
				try:
					baytech = BayTechGeorgeTown(values, verbose, ['22', '23'])
					rb_ret = baytech.reboot(values[nodename], dryrun)
				except:
					baytech = BayTechGeorgeTown(values, verbose, ['22', '23'])
					rb_ret = baytech.reboot(values[nodename], dryrun)
			else:
				baytech = BayTech(values, verbose, ['22', '23'])
				rb_ret = baytech.reboot(values[nodename], dryrun)

		# iLO
		elif continue_probe and values['model'].find("ilo") >= 0:
			try:
				hpilo = HPiLO(values, verbose, ['22'])
				rb_ret = hpilo.reboot(0, dryrun)
				if rb_ret != 0:
					hpilo = HPiLOHttps(values, verbose, ['443'])
					rb_ret = hpilo.reboot(0, dryrun)
			except:
				hpilo = HPiLOHttps(values, verbose, ['443'])
				rb_ret = hpilo.reboot(0, dryrun)

		# DRAC ssh
		elif continue_probe and values['model'].find("DRAC") >= 0:
			# TODO: I don't think DRACRacAdm will throw an exception for the
			# default method to catch...
			try:
				if values['pcu_id'] in [1402]:
					drac = DRAC(values, verbose, ['22'])
					rb_ret = drac.reboot(0, dryrun)
				else:
					drac = DRACRacAdm(values, verbose, ['443', '5869'])
					rb_ret = drac.reboot(0, dryrun)
			except:
				drac = DRAC(values, verbose, ['22'])
				rb_ret = drac.reboot(0, dryrun)

		elif continue_probe and values['model'].find("WTI IPS-4") >= 0:
				wti = WTIIPS4(values, verbose, ['23'])
				rb_ret = wti.reboot(values[nodename], dryrun)

		elif continue_probe and values['model'].find("AMT") >= 0:
				amt = IntelAMT(values, verbose, ['16992'])
				rb_ret = amt.reboot(values[nodename], dryrun)

		# BlackBox PSExxx-xx (e.g. PSE505-FR)
		elif continue_probe and values['model'].find("ePowerSwitch") >=0:
			# TODO: allow a different port than http 80.
			if values['pcu_id'] in [1089, 1071, 1046, 1035, 1118]:
				eps = ePowerSwitchGood(values, verbose, ['80'])
			elif values['pcu_id'] in [1003]:
				# OLD EPOWER
				print "OLD EPOWER"
				eps = ePowerSwitch(values, verbose, ['80'])
			else:
				eps = ePowerSwitchGood(values, verbose, ['80'])

			rb_ret = eps.reboot(values[nodename], dryrun)
		elif continue_probe and values['pcu_id'] in [1122]:
			custom = CustomPCU(values, verbose, ['80', '443'])
			custom.reboot(values[nodename], dryrun)

		elif continue_probe:
			rb_ret = "Unsupported_PCU"

		elif continue_probe == False:
			if 'portstatus' in values:
				rb_ret = "NetDown"
			else:
				rb_ret = "Not_Run"
		else:
			rb_ret = -1

	except ExceptionPort, err:
		rb_ret = str(err)

	return rb_ret
	# ????
	#elif continue_probe and values['protocol'] == "racadm" and \
	#		values['model'] == "RAC":
	#	rb_ret = racadm_reboot(pcu_name(values),
	#								  values['username'],
	#								  values['password'],
	#								  pcu[nodename],
	#								  dryrun)

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
	import plc
	logger = logging.getLogger("monitor")
	main()
