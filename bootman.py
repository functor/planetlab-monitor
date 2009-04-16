#!/usr/bin/python

# Attempt to reboot a node in debug state.



import os
import sys
import time
import random
import signal
import traceback
import subprocess
from sets import Set

from getsshkeys import SSHKnownHosts

from Rpyc import SocketConnection, Async
from Rpyc.Utils import *

import getconf
from monitor import config
from monitor import const
from monitor.model import *
from monitor.common import email_exception, found_within
from monitor.database.info.model import *
from monitor.database.info.interface import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.wrapper.emailTxt import mailtxt

from pcucontrol.util import command as moncommands
from pcucontrol.util.command import Sopen
from pcucontrol.transports.ssh import pxssh as pxssh
from pcucontrol.transports.ssh import fdpexpect as fdpexpect
from pcucontrol.transports.ssh import pexpect as pexpect

from nodeconfig import network_config_to_str


api = plc.getAuthAPI()
fb = None


class NodeConnection:
	def __init__(self, connection, node, config):
		self.node = node
		self.c = connection
		self.config = config

	def get_boot_state(self):
		try:
			if self.c.modules.os.path.exists('/tmp/source'):
				return "debug"
			elif self.c.modules.os.path.exists('/vservers'): 
				return "boot"
			else:
				return "unknown"
		except EOFError:
			traceback.print_exc()
			print self.c.modules.sys.path
		except:
			email_exception()
			traceback.print_exc()

		return "unknown"

	def get_dmesg(self):
		self.c.modules.os.system("dmesg > /var/log/dmesg.bm.log")
		download(self.c, "/var/log/dmesg.bm.log", "log/dmesg.%s.log" % self.node)
		log = open("log/dmesg.%s.log" % self.node, 'r')
		return log

	def get_bootmanager_log(self):
		download(self.c, "/tmp/bm.log", "log/bm.%s.log.gz" % self.node)
		#os.system("zcat log/bm.%s.log.gz > log/bm.%s.log" % (self.node, self.node))
		os.system("cp log/bm.%s.log.gz log/bm.%s.log" % (self.node, self.node))
		log = open("log/bm.%s.log" % self.node, 'r')
		return log

	def dump_plconf_file(self):
		c = self.c
		self.c.modules.sys.path.append("/tmp/source/")
		self.c.modules.os.chdir('/tmp/source')

		log = c.modules.BootManager.log('/tmp/new.log')
		bm = c.modules.BootManager.BootManager(log,'boot')

		BootManagerException = c.modules.Exceptions.BootManagerException
		InitializeBootManager = c.modules.BootManager.InitializeBootManager
		ReadNodeConfiguration = c.modules.BootManager.ReadNodeConfiguration
		bm_continue = True

		InitializeBootManager.Run(bm.VARS, bm.LOG)
		try: ReadNodeConfiguration.Run(bm.VARS, bm.LOG)
		except Exception, x:
			bm_continue = False
			print "   ERROR:", x
			print "   Possibly, unable to find valid configuration file"

		if bm_continue:
			for key in bm.VARS.keys():
				print key, " == ", bm.VARS[key]
		else:
			print "   Unable to read Node Configuration"
		

	def compare_and_repair_nodekeys(self):
		c = self.c
		self.c.modules.sys.path.append("/tmp/source/")
		self.c.modules.os.chdir('/tmp/source')

		log = c.modules.BootManager.log('/tmp/new.log')
		bm = c.modules.BootManager.BootManager(log,'boot')

		BootManagerException = c.modules.Exceptions.BootManagerException
		InitializeBootManager = c.modules.BootManager.InitializeBootManager
		ReadNodeConfiguration = c.modules.BootManager.ReadNodeConfiguration
		bm_continue = True

		plcnode = plccache.GetNodeByName(self.node)

		InitializeBootManager.Run(bm.VARS, bm.LOG)
		try: ReadNodeConfiguration.Run(bm.VARS, bm.LOG)
		except Exception, x:
			bm_continue = False
			print "exception"
			print x
			print "   Possibly, unable to find valid configuration file"

		if bm_continue:
			print "   NODE: %s" % bm.VARS['NODE_KEY']
			print "   PLC : %s" % plcnode['key']

			if bm.VARS['NODE_KEY'] == plcnode['key']:
				return True
			else:
				if api.UpdateNode(self.node, {'key': bm.VARS['NODE_KEY']}):
					print "   Successfully updated NODE_KEY with PLC"
					return True
				else:
					return False
				
			#for key in bm.VARS.keys():
			#	print key, " == ", bm.VARS[key]
		else:
			print "   Unable to retrieve NODE_KEY"

	def bootmanager_running(self):
		if self.c.modules.os.path.exists('/tmp/BM_RUNNING'):
			return True
		else:
			return False

	def set_nodestate(self, state='boot'):
		return api.UpdateNode(self.node, {'boot_state' : state})

	def restart_node(self, state='boot'):
		api.UpdateNode(self.node, {'boot_state' : state})

		pflags = PersistFlags(self.node, 1*60*60*24, db='restart_persistflags')
		if not pflags.getRecentFlag('gentlekill'):
			print "   Killing all slice processes... : %s" %  self.node
			cmd_slicekill = "ls -d /proc/virtual/[0-9]* | awk -F '/' '{print $4}' | xargs -I{} /usr/sbin/vkill -s 9 --xid {} -- 0"
			self.c.modules.os.system(cmd_slicekill)
			cmd = """ shutdown -r +1 & """
			print "   Restarting %s : %s" % ( self.node, cmd)
			self.c.modules.os.system(cmd)

			pflags.setRecentFlag('gentlekill')
			pflags.save()
		else:
			print "   Restarting with sysrq 'sub' %s" % self.node
			cmd = """ (sleep 5; echo 's' > /proc/sysrq-trigger; echo 'u' > /proc/sysrq-trigger; echo 'b' > /proc/sysrq-trigger ) & """
			self.c.modules.os.system(cmd)

		return

	def restart_bootmanager(self, forceState):

		self.c.modules.os.chdir('/tmp/source')
		if self.c.modules.os.path.exists('/tmp/BM_RUNNING'):
			print "   BootManager is already running: try again soon..."
		else:
			print "   Starting 'BootManager.py %s' on %s " % (forceState, self.node)
			cmd = "( touch /tmp/BM_RUNNING ;  " + \
			      "  python ./BootManager.py %s &> server.log < /dev/null ; " + \
				  "  rm -f /tmp/BM_RUNNING " + \
				  ") &" 
			cmd = cmd % forceState
			self.c.modules.os.system(cmd)

		return 


class PlanetLabSession:
	globalport = 22000 + int(random.random()*1000)

	def __init__(self, node, nosetup, verbose):
		self.verbose = verbose
		self.node = node
		self.port = None
		self.nosetup = nosetup
		self.command = None
		self.setup_host()

	def get_connection(self, config):
		conn = NodeConnection(SocketConnection("localhost", self.port), self.node, config)
		#i = 0
		#while i < 3: 
		#	print i, conn.c.modules.sys.path
		#	print conn.c.modules.os.path.exists('/tmp/source')
		#	i+=1
		#	time.sleep(1)
		return conn
	
	def setup_host(self):
		self.port = PlanetLabSession.globalport
		PlanetLabSession.globalport = PlanetLabSession.globalport + 1

		args = {}
		args['port'] = self.port
		args['user'] = 'root'
		args['hostname'] = self.node
		args['monitordir'] = config.MONITOR_SCRIPT_ROOT
		ssh_port = 22

		if self.nosetup:
			print "Skipping setup"
			return 

		# COPY Rpyc files to host
		cmd = "rsync -qv -az -e ssh %(monitordir)s/Rpyc/ %(user)s@%(hostname)s:Rpyc 2> /dev/null" % args
		if self.verbose: print cmd
		print cmd
		# TODO: Add timeout
		timeout = 120
		localos = moncommands.CMD()

		ret = localos.system(cmd, timeout)
		print ret
		if ret != 0:
			print "\tUNKNOWN SSH KEY FOR %s; making an exception" % self.node
			#print "MAKE EXPLICIT EXCEPTION FOR %s" % self.node
			k = SSHKnownHosts(); k.updateDirect(self.node); k.write(); del k
			ret = localos.system(cmd, timeout)
			print ret
			if ret != 0:
				print "\tFAILED TWICE"
				#sys.exit(1)
				raise Exception("Failed twice trying to login with updated ssh host key")

		t1 = time.time()
		# KILL any already running servers.
		ssh = moncommands.SSH(args['user'], args['hostname'], ssh_port)
		(ov,ev) = ssh.run_noexcept2("""<<\EOF
            rm -f out.log
            echo "kill server" >> out.log
            ps ax | grep Rpyc | grep -v grep | awk '{print $1}' | xargs kill 2> /dev/null ; 
            echo "export" >> out.log
            export PYTHONPATH=$HOME  ;
            echo "start server" >> out.log
            python Rpyc/Servers/forking_server.py &> server.log &
            echo "done" >> out.log
EOF""")
		#cmd = """ssh %(user)s@%(hostname)s """ + \
		#	 """'ps ax | grep Rpyc | grep -v grep | awk "{print \$1}" | xargs kill 2> /dev/null' """
		#cmd = cmd % args
		#if self.verbose: print cmd
		## TODO: Add timeout
		#print localos.system(cmd,timeout)

		## START a new rpyc server.
		#cmd = """ssh -n %(user)s@%(hostname)s "export PYTHONPATH=\$HOME; """ + \
		#	 """python Rpyc/Servers/forking_server.py &> server.log < /dev/null &" """ 
		#cmd = cmd % args
		#if self.verbose: print cmd
		#print localos.system(cmd,timeout)
		print "setup rpyc server over ssh"
		print ssh.ret

		# TODO: Add timeout
		# This was tricky to make synchronous.  The combination of ssh-clients-4.7p1, 
		# and the following options seems to work well.
		cmd = """ssh -o ExitOnForwardFailure=yes -o BatchMode=yes """ + \
			  """-o PermitLocalCommand=yes -o LocalCommand='echo "READY"' """ + \
			  """-o ConnectTimeout=120 """ + \
			  """-n -N -L %(port)s:localhost:18812 """ + \
			  """%(user)s@%(hostname)s"""
		cmd = cmd % args
		if self.verbose: print cmd
		print cmd
		self.command = Sopen(cmd, shell=True, stdout=subprocess.PIPE)
		# TODO: the read() here may block indefinitely.  Need a better
		# approach therefore, that includes a timeout.
		#ret = self.command.stdout.read(5)
		ret = moncommands.read_t(self.command.stdout, 5)

		t2 = time.time()
		if 'READY' in ret:
			# NOTE: There is still a slight race for machines that are slow...
			self.timeout = 2*(t2-t1)
			print "Sleeping for %s sec" % self.timeout
			time.sleep(self.timeout)
			return

		if self.command.returncode is not None:
			print "Failed to establish tunnel!"
			raise Exception("SSH Tunnel exception : %s %s" % (self.node, self.command.returncode))

		raise Exception("Unknown SSH Tunnel Exception: still running, but did not report 'READY'")

	def __del__(self):
		if self.command:
			if self.verbose: print "Killing SSH session %s" % self.port
			print "Killing SSH session %s" % self.port
			self.command.kill()

	
def steps_to_list(steps, index=1):
	return map(lambda x: x[index], steps)

def index_to_id(steps,index):
	if index < len(steps):
		return steps[index][0]
	else:
		return "done"

class DebugInterface:
	def __init__(self, hostname):
		self.hostname = hostname
		self.session = None

	def getConnection(self):
		print "Creating session for %s" % self.hostname
		# update known_hosts file (in case the node has rebooted since last run)
		try:
			k = SSHKnownHosts(); k.update(self.hostname); k.write(); del k
		except:
			email_exception()
			print traceback.print_exc()
			return False

		try:
			if config == None:
				self.session = PlanetLabSession(self.hostname, False, True)
			else:
				self.session = PlanetLabSession(self.hostname, config.nosetup, config.verbose)
		except Exception, e:
			msg = "ERROR setting up session for %s" % self.hostname
			print msg
			traceback.print_exc()
			email_exception(msg)
			return False

		try:
			conn = self.session.get_connection(config)
		except EOFError:
			# NOTE: sometimes the wait in setup_host() is not long enough.  
			# So, here we try to wait a little longer before giving up entirely.
			try:
				time.sleep(self.session.timeout*5)
				conn = self.session.get_connection(config)
			except:
				traceback.print_exc()
				email_exception(self.hostname)
				return False
		#print "trying to use conn before returning it."
		#print conn.c.modules.sys.path
		#print conn.c.modules.os.path.exists('/tmp/source')
		#time.sleep(1)

		#print "conn: %s" % conn
		return conn

	def getSequences(self):

		# TODO: This can be replaced with a DB definition at a future time.
		# 		This would make it possible for an admin to introduce new
		# 		patterns without touching code.
		
		sequences = {}
		# restart_bootmanager_boot
		for n in ["bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-protoerror-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-implementerror-bootupdatefail-update-debug-done",

				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-exception-protoerror-update-protoerror-debug-done",

				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-debug-done",
				"bminit-cfg-auth-getplc-exception-protoerror-update-protoerror-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-protoerror-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-bootupdatefail-authfail-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-debug-done",
				"bminit-cfg-auth-getplc-exception-protoerror-update-debug-done",
				"bminit-cfg-auth-getplc-implementerror-update-debug-done",
				]:
			sequences.update({n : "restart_bootmanager_boot"})

		#	conn.restart_bootmanager('rins')
		for n in [ "bminit-cfg-auth-getplc-installinit-validate-exception-modulefail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-modulefail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-bziperror-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nofilereference-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-exception-mkfsfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-installcfg-installstop-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-kernelcopyfail-exception-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-installcfg-installstop-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-kernelcopyfail-exception-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-exception-noinstall-update-debug-done",
				# actual solution appears to involve removing the bad files, and
				# continually trying to boot the node.
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-implementerror-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-exception-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-bmexceptmount-exception-noinstall-update-debug-done",
				]:
			sequences.update({n : "restart_bootmanager_rins"})

		# repair_node_keys
		sequences.update({"bminit-cfg-auth-bootcheckfail-authfail-exception-update-bootupdatefail-authfail-debug-done": "repair_node_keys"})

		#   conn.restart_node('rins')
		for n in ["bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-installcfg-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-writeerror-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-exception-bmexceptrmfail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-exception-bmexceptrmfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-implementerror-bootupdatefail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-readonlyfs-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-nospace-exception-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nospace-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-exception-downloadfail-update-debug-done",
				]:
			sequences.update({n : "restart_node_rins"})

		#	restart_node_boot
		for n in ["bminit-cfg-auth-getplc-implementerror-bootupdatefail-update-debug-done",
				 "bminit-cfg-auth-implementerror-bootcheckfail-update-debug-done",
				 "bminit-cfg-auth-implementerror-bootcheckfail-update-implementerror-bootupdatefail-done",
				 "bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nospace-update-debug-done",
				 "bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-exception-downloadfail-update-debug-done",
				 "bminit-cfg-auth-getplc-update-installinit-validate-implementerror-update-debug-done",
				 ]:
			sequences.update({n: "restart_node_boot"})

		# update_node_config_email
		for n in ["bminit-cfg-exception-nocfg-update-bootupdatefail-nonode-debug-done",
				  "bminit-cfg-exception-update-bootupdatefail-nonode-debug-done",
				  "bminit-cfg-auth-bootcheckfail-nonode-exception-update-bootupdatefail-nonode-debug-done",
				]:
			sequences.update({n : "update_node_config_email"})

		for n in [ "bminit-cfg-exception-nodehostname-update-debug-done", 
				   "bminit-cfg-update-exception-nodehostname-update-debug-done", 
				]:
			sequences.update({n : "nodenetwork_email"})

		# update_bootcd_email
		for n in ["bminit-cfg-auth-getplc-update-hardware-exception-noblockdev-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-exception-noblockdev-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-noblockdev-exception-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-noblockdev-exception-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-exception-hardwarerequirefail-update-debug-done",
				]:
			sequences.update({n : "update_bootcd_email"})

		for n in [ "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nofilereference-update-debug-done",
				]:
			sequences.update({n: "suspect_error_email"})

		# update_hardware_email
		sequences.update({"bminit-cfg-auth-getplc-hardware-exception-disktoosmall-hardwarerequirefail-update-debug-done" : "update_hardware_email"})
		sequences.update({"bminit-cfg-auth-getplc-hardware-disktoosmall-exception-hardwarerequirefail-update-debug-done" : "update_hardware_email"})

		# broken_hardware_email
		sequences.update({"bminit-cfg-auth-getplc-update-hardware-exception-hardwarerequirefail-update-debug-done" : "broken_hardware_email"})

		# bad_dns_email
		for n in [ 
		 "bminit-cfg-update-implementerror-bootupdatefail-dnserror-update-implementerror-bootupdatefail-dnserror-done",
			"bminit-cfg-auth-implementerror-bootcheckfail-dnserror-update-implementerror-bootupdatefail-dnserror-done",
			]:
			sequences.update( { n : "bad_dns_email"})

		return sequences

	def getDiskSteps(self):
		steps = [
			('scsierror'  , 'SCSI error : <\d+ \d+ \d+ \d+> return code = 0x\d+'),
			('ioerror'    , 'end_request: I/O error, dev sd\w+, sector \d+'),
			('ccisserror' , 'cciss: cmd \w+ has CHECK CONDITION  byte \w+ = \w+'),

			('buffererror', 'Buffer I/O error on device dm-\d, logical block \d+'),

			('hdaseekerror', 'hda: dma_intr: status=0x\d+ { DriveReady SeekComplete Error }'),
			('hdacorrecterror', 'hda: dma_intr: error=0x\d+ { UncorrectableError }, LBAsect=\d+, sector=\d+'),

			('atareadyerror'   , 'ata\d+: status=0x\d+ { DriveReady SeekComplete Error }'),
			('atacorrecterror' , 'ata\d+: error=0x\d+ { UncorrectableError }'),

			('sdXerror'   , 'sd\w: Current: sense key: Medium Error'),
			('ext3error'   , 'EXT3-fs error (device dm-\d+): ext3_find_entry: reading directory #\d+ offset \d+'),

			('floppytimeout','floppy0: floppy timeout called'),
			('floppyerror',  'end_request: I/O error, dev fd\w+, sector \d+'),

			# hda: dma_intr: status=0x51 { DriveReady SeekComplete Error }
			# hda: dma_intr: error=0x40 { UncorrectableError }, LBAsect=23331263, sector=23331263

			# floppy0: floppy timeout called
			# end_request: I/O error, dev fd0, sector 0

			# Buffer I/O error on device dm-2, logical block 8888896
			# ata1: status=0x51 { DriveReady SeekComplete Error }
			# ata1: error=0x40 { UncorrectableError }
			# SCSI error : <0 0 0 0> return code = 0x8000002
			# sda: Current: sense key: Medium Error
			#	Additional sense: Unrecovered read error - auto reallocate failed

			# SCSI error : <0 2 0 0> return code = 0x40001
			# end_request: I/O error, dev sda, sector 572489600
		]
		return steps

	def getDiskSequence(self, steps, child):
		sequence = []
		while True:
			id = index_to_id(steps, child.expect( steps_to_list(steps) + [ pexpect.EOF ]))
			sequence.append(id)

			if id == "done":
				break
		return sequence

	def getBootManagerStepPatterns(self):
		steps = [
			('bminit' 		, 'Initializing the BootManager.'),
			('cfg'			, 'Reading node configuration file.'),
			('auth'			, 'Authenticating node with PLC.'),
			('getplc'		, 'Retrieving details of node from PLC.'),
			('update'		, 'Updating node boot state at PLC.'),
			('hardware'		, 'Checking if hardware requirements met.'),
			('installinit'	, 'Install: Initializing.'),
			('installdisk'	, 'Install: partitioning disks.'),
			('installbootfs', 'Install: bootstrapfs tarball.'),
			('installcfg'	, 'Install: Writing configuration files.'),
			('installstop'	, 'Install: Shutting down installer.'),
			('update2'		, 'Updating node boot state at PLC.'),
			('installinit2'	, 'Install: Initializing.'),
			('validate'		, 'Validating node installation.'),
			('rebuildinitrd', 'Rebuilding initrd'),
			('netcfg'		, 'Install: Writing Network Configuration files.'),
			('update3'		, 'Updating node configuration.'),
			('disk'			, 'Checking for unused disks to add to LVM.'),
			('update4'		, 'Sending hardware configuration to PLC.'),
			('debug'		, 'Starting debug mode'),
			('bmexceptmount', 'BootManagerException during mount'),
			('bmexceptvgscan', 'BootManagerException during vgscan/vgchange'),
			('bmexceptrmfail', 'Unable to remove directory tree: /tmp/mnt'),
			('exception'	, 'Exception'),
			('nocfg'        , 'Found configuration file planet.cnf on floppy, but was unable to parse it.'),
			('protoerror'   , 'XML RPC protocol error'),
			('nodehostname' , 'Configured node hostname does not resolve'),
			('implementerror', 'Implementation Error'),
			('readonlyfs'   , '[Errno 30] Read-only file system'),
			('baddisk'      , "IOError: [Errno 13] Permission denied: '/tmp/mnt/sysimg//vservers/\w+/etc/hosts'"),
			('noinstall'    , 'notinstalled'),
			('bziperror'    , 'bzip2: Data integrity error when decompressing.'),
			('noblockdev'   , "No block devices detected."),
			('dnserror'     , 'Name or service not known'),
			('downloadfail' , 'Unable to download main tarball /boot/bootstrapfs-planetlab-i386.tar.bz2 from server.'),
			('disktoosmall' , 'The total usable disk size of all disks is insufficient to be usable as a PlanetLab node.'),
			('hardwarerequirefail' , 'Hardware requirements not met'),
			('mkfsfail'	    , 'while running: Running mkfs.ext2 -q  -m 0 -j /dev/planetlab/vservers failed'),
			('nofilereference', "No such file or directory: '/tmp/mnt/sysimg//vservers/.vref/planetlab-f8-i386/etc/hosts'"),
			('kernelcopyfail', "cp: cannot stat `/tmp/mnt/sysimg/boot/kernel-boot': No such file or directory"),
			('chrootfail'   , 'Running chroot /tmp/mnt/sysimg'),
			('modulefail'   , 'Unable to get list of system modules'),
			('writeerror'   , 'write error: No space left on device'),
			('nospace'      , "No space left on device"),
			('nonode'       , 'Failed to authenticate call: No such node'),
			('authfail'     , 'Failed to authenticate call: Call could not be authenticated'),
			('bootcheckfail'     , 'BootCheckAuthentication'),
			('bootupdatefail'   , 'BootUpdateNode'),
		]
		return steps

	def getBootManagerSequenceFromLog(self, steps, child):
		sequence = []
		while True:
			
			index = child.expect( steps_to_list(steps) + [ pexpect.EOF ])
			id = index_to_id(steps,index)
			sequence.append(id)

			if id == "exception":
				print "...Found An Exception!!!"
			elif id == "done": #index == len(steps_to_list(steps)):
				#print "Reached EOF"
				break

		return sequence
		

def restore(sitehist, hostname, config=None, forced_action=None):

	# NOTE: Nothing works if the bootcd is REALLY old.
	#       So, this is the first step.

	fbnode = FindbadNodeRecord.get_latest_by(hostname=hostname).to_dict()
	recent_actions = sitehist.getRecentActions(hostname=hostname)

	if fbnode['observed_category'] == "OLDBOOTCD":
		print "\t...Notify owner to update BootImage!!!"

		if not found_within(recent_actions, 'newbootcd_notice', 3):
			sitehist.sendMessage('newbootcd_notice', hostname=hostname)

			print "\tDisabling %s due to out-of-date BootImage" % hostname
			api.UpdateNode(hostname, {'boot_state' : 'disable'})

		# NOTE: nothing else is possible.
		return True

	debugnode = DebugInterface(hostname)
	conn = debugnode.getConnection()
	#print "conn: %s" % conn
	#print "trying to use conn after returning it."
	#print conn.c.modules.sys.path
	#print conn.c.modules.os.path.exists('/tmp/source')
	if type(conn) == type(False): return False

	#if forced_action == "reboot":
	#	conn.restart_node('rins')
	#	return True

	boot_state = conn.get_boot_state()
	if boot_state != "debug":
		print "... %s in %s state: skipping..." % (hostname , boot_state)
		return boot_state == "boot"

	if conn.bootmanager_running():
		print "...BootManager is currently running.  Skipping host %s" %hostname 
		return True

	# Read persistent flags, tagged on one week intervals.

	if config and not config.quiet: print "...downloading dmesg from %s" %hostname 
	dmesg = conn.get_dmesg()
	child = fdpexpect.fdspawn(dmesg)

	steps = debugnode.getDiskSteps()
	sequence = debugnode.getDiskSequence(steps, child)

	s = Set(sequence)
	if config and not config.quiet: print "\tSET: ", s

	if len(s) > 1:
		print "...Potential drive errors on %s" % hostname 
		if len(s) == 2 and 'floppyerror' in s:
			print "...Should investigate.  Continuing with node."
		else:
			print "...Should investigate.  Skipping node."
			# TODO: send message related to these errors.

			if not found_within(recent_actions, 'newbootcd_notice', 3):

				log=conn.get_dmesg().read()
				sitehist.sendMessage('baddisk_notice', hostname=hostname, log=log)
				conn.set_nodestate('disable')

			return False

	print "...Downloading bm.log from %s" %hostname 
	log = conn.get_bootmanager_log()
	child = fdpexpect.fdspawn(log)

	if hasattr(config, 'collect') and config.collect: return True

	if config and not config.quiet: print "...Scanning bm.log for errors"

	time.sleep(1)

	steps = debugnode.getBootManagerStepPatterns()
	sequence = debugnode.getBootManagerSequenceFromLog(steps, child)
		
	s = "-".join(sequence)
	print "   FOUND SEQUENCE: ", s

	# NOTE: We get or set the flag based on the current sequence identifier.
	#  By using the sequence identifier, we guarantee that there will be no
	#  frequent loops.  I'm guessing there is a better way to track loops,
	#  though.

	sequences = debugnode.getSequences()
	flag_set = True
	
	if s not in sequences:
		print "   HOST %s" % hostname
		print "   UNKNOWN SEQUENCE: %s" % s

		args = {}
		args['hostname'] = hostname
		args['sequence'] = s
		args['bmlog'] = conn.get_bootmanager_log().read()
		args['viart'] = False

		sitehist.sendMessage('unknownsequence_notice', **args)

		conn.restart_bootmanager('boot')

		# NOTE: Do not set the pflags value for this sequence if it's unknown.
		# This way, we can check it again after we've fixed it.
		flag_set = False

	else:

		if   sequences[s] == "restart_bootmanager_boot":
			print "...Restarting BootManager.py on %s "%hostname 
			conn.restart_bootmanager('boot')
		elif sequences[s] == "restart_bootmanager_rins":
			print "...Restarting BootManager.py on %s "%hostname 
			conn.restart_bootmanager('rins')
		elif sequences[s] == "restart_node_rins":
			conn.restart_node('rins')
		elif sequences[s] == "restart_node_boot":
			conn.restart_node('boot')
		elif sequences[s] == "repair_node_keys":
			if conn.compare_and_repair_nodekeys():
				# the keys either are in sync or were forced in sync.
				# so try to reboot the node again.
				conn.restart_bootmanager('rins')
				pass
			else:
				# there was some failure to synchronize the keys.
				print "...Unable to repair node keys on %s" %hostname 

		elif sequences[s] == "suspect_error_email":
			args = {}
			args['hostname'] = hostname
			args['sequence'] = s
			args['bmlog'] = conn.get_bootmanager_log().read()
			args['viart'] = False

			sitehist.sendMessage('unknownsequence_notice', **args)
			conn.restart_bootmanager('boot')

		# TODO: differentiate this and the 'nodenetwork_email' actions.
		elif sequences[s] == "update_node_config_email":

			if not found_within(recent_actions, 'nodeconfig_notice', 3):
				args = {}
				args['hostname'] = hostname
				sitehist.sendMessage('nodeconfig_notice', **args)
				conn.dump_plconf_file()

		elif sequences[s] == "nodenetwork_email":

			if not found_within(recent_actions, 'nodeconfig_notice', 3):
				args = {}
				args['hostname'] = hostname
				args['bmlog'] = conn.get_bootmanager_log().read()
				sitehist.sendMessage('nodeconfig_notice', **args)
				conn.dump_plconf_file()

		elif sequences[s] == "update_bootcd_email":

			if not found_within(recent_actions, 'newalphacd_notice', 3):
				args = {}
				args.update(getconf.getconf(hostname)) # NOTE: Generates boot images for the user:
				args['hostname'] = hostname
			
				sitehist.sendMessage('newalphacd_notice', **args)

				print "\tDisabling %s due to out-of-date BOOTCD" % hostname

		elif sequences[s] == "broken_hardware_email":
			# MAKE An ACTION record that this host has failed hardware.  May
			# require either an exception "/minhw" or other manual intervention.
			# Definitely need to send out some more EMAIL.
			# TODO: email notice of broken hardware
			if not found_within(recent_actions, 'baddisk_notice', 1):
				print "...NOTIFYING OWNERS OF BROKEN HARDWARE on %s!!!" % hostname
				args = {}
				args['hostname'] = hostname
				args['log'] = conn.get_dmesg().read()

				sitehist.sendMessage('baddisk_notice', **args)
				conn.set_nodestate('disable')

		elif sequences[s] == "update_hardware_email":
			if not found_within(recent_actions, 'minimalhardware_notice', 1):
				print "...NOTIFYING OWNERS OF MINIMAL HARDWARE FAILURE on %s!!!" % hostname
				args = {}
				args['hostname'] = hostname
				args['bmlog'] = conn.get_bootmanager_log().read()
				sitehist.sendMessage('minimalhardware_notice', **args)

		elif sequences[s] == "bad_dns_email":
			if not found_within(recent_actions, 'baddns_notice', 1):
				print "...NOTIFYING OWNERS OF DNS FAILURE on %s!!!" % hostname
				args = {}
				try:
					node = plccache.GetNodeByName(hostname)
					net = api.GetNodeNetworks(node['nodenetwork_ids'])[0]
				except:
					email_exception()
					print traceback.print_exc()
					# TODO: api error. skip email, b/c all info is not available,
					# flag_set will not be recorded.
					return False
				nodenet_str = network_config_to_str(net)

				args['hostname'] = hostname
				args['network_config'] = nodenet_str
				args['nodenetwork_id'] = net['nodenetwork_id']

				sitehist.sendMessage('baddns_notice', **args)

	return True
	

# MAIN -------------------------------------------------------------------

def main():
	from monitor import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(child=False, collect=False, nosetup=False, verbose=False, 
						force=None, quiet=False)
	parser.add_option("", "--child", dest="child", action="store_true", 
						help="This is the child mode of this process.")
	parser.add_option("", "--force", dest="force", metavar="boot_state",
						help="Force a boot state passed to BootManager.py.")
	parser.add_option("", "--quiet", dest="quiet", action="store_true", 
						help="Extra quiet output messages.")
	parser.add_option("", "--verbose", dest="verbose", action="store_true", 
						help="Extra debug output messages.")
	parser.add_option("", "--nonet", dest="nonet", action="store_true", 
						help="Do not setup the network, use existing log files to re-run a test pass.")
	parser.add_option("", "--collect", dest="collect", action="store_true", 
						help="No action, just collect dmesg, and bm.log")
	parser.add_option("", "--nosetup", dest="nosetup", action="store_true", 
						help="Do not perform the orginary setup phase.")

	parser = parsermodule.getParser(['nodesets', 'defaults'], parser)
	config = parsermodule.parse_args(parser)

	if config.nodelist:
		nodes = config.getListFromFile(config.nodelist)
	elif config.node:
		nodes = [ config.node ]
	else:
		parser.print_help()
		sys.exit(1)

	for node in nodes:
		# get sitehist
		lb = plccache.plcdb_hn2lb[node]
		sitehist = SiteInterface.get_or_make(loginbase=lb)
		#reboot(node, config)
		restore(sitehist, node, config=None, forced_action=None)

if __name__ == "__main__":
	main()
