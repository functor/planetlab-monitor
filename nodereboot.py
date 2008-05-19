#!/usr/bin/python

# Attempt to reboot a node in debug state.


import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import sys
import os

from getsshkeys import SSHKnownHosts

import subprocess
import time
import soltesz
from sets import Set

import ssh.pxssh as pxssh
import ssh.fdpexpect as fdpexpect
import ssh.pexpect as pexpect



import signal
class Sopen(subprocess.Popen):
	def kill(self, signal = signal.SIGTERM):
		os.kill(self.pid, signal)

#from Rpyc import SocketConnection, Async
from Rpyc import SocketConnection, Async
from Rpyc.Utils import *


class NodeConnection:
	def __init__(self, connection, node, config):
		self.node = node
		self.c = connection
		self.config = config

	def get_boot_state(self):
		if self.c.modules.os.path.exists('/tmp/source'):
			return "dbg"
		elif self.c.modules.os.path.exists('/vservers'): 
			return "boot"
		else:
			return "unknown"

	def get_dmesg(self):
		self.c.modules.os.system("dmesg > /var/log/dmesg.bm.log")
		download(self.c, "/var/log/dmesg.bm.log", "log/dmesg.%s.log" % self.node)
		log = open("log/dmesg.%s.log" % self.node, 'r')
		return log

	def get_bootmanager_log(self):
		download(self.c, "/tmp/bm.log", "log/bm.%s.log.gz" % self.node)
		os.system("zcat log/bm.%s.log.gz > log/bm.%s.log" % (self.node, self.node))
		log = open("log/bm.%s.log" % self.node, 'r')
		return log

	def dump_plconf_file(self):
		c = self.c
		c.modules.sys.path.append("/tmp/source/")
		c.modules.os.chdir('/tmp/source')

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

		if bm_continue and self.config and not self.config.quiet:
			for key in bm.VARS.keys():
				print key, " == ", bm.VARS[key]
		else:
			if self.config and not self.config.quiet: print "   Unable to read Node Configuration"
		

	def compare_and_repair_nodekeys(self):
		c = self.c
		c.modules.sys.path.append("/tmp/source/")
		c.modules.os.chdir('/tmp/source')

		log = c.modules.BootManager.log('/tmp/new.log')
		bm = c.modules.BootManager.BootManager(log,'boot')

		BootManagerException = c.modules.Exceptions.BootManagerException
		InitializeBootManager = c.modules.BootManager.InitializeBootManager
		ReadNodeConfiguration = c.modules.BootManager.ReadNodeConfiguration
		bm_continue = True

		plcnode = api.GetNodes({'hostname': self.node}, None)[0]

		InitializeBootManager.Run(bm.VARS, bm.LOG)
		try: ReadNodeConfiguration.Run(bm.VARS, bm.LOG)
		except Exception, x:
			bm_continue = False
			if not config.quiet: print "exception"
			if not config.quiet: print x
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

	def restart_node(self, state='boot'):
		api.UpdateNode(self.node, {'boot_state' : state})

		print "   Killing all slice processes... : %s" %  self.node
		cmd_slicekill = "ls -d /proc/virtual/[0-9]* | awk -F '/' '{print $4}' | xargs -I{} /usr/sbin/vkill -s 9 --xid {} -- 0"
		self.c.modules.os.system(cmd_slicekill)

		cmd = """ shutdown -r +1 & """
		print "   Restarting %s : %s" % ( self.node, cmd)
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
	globalport = 22222

	def __init__(self, node, nosetup, verbose):
		self.verbose = verbose
		self.node = node
		self.port = None
		self.nosetup = nosetup
		self.command = None
		self.setup_host()

	def get_connection(self, config):
		return NodeConnection(SocketConnection("localhost", self.port), self.node, config)
	
	def setup_host(self):
		self.port = PlanetLabSession.globalport
		PlanetLabSession.globalport = PlanetLabSession.globalport + 1

		args = {}
		args['port'] = self.port
		args['user'] = 'root'
		args['hostname'] = self.node
		args['monitordir'] = "/home/soltesz/monitor"

		if self.nosetup:
			print "Skipping setup"
			return 

		# COPY Rpyc files to host
		cmd = "rsync -qv -az -e ssh %(monitordir)s/Rpyc-2.45-2.3/ %(user)s@%(hostname)s:Rpyc 2> /dev/null" % args
		if self.verbose: print cmd
		ret = os.system(cmd)
		if ret != 0:
			print "UNKNOWN SSH KEY FOR %s" % self.node
			print "MAKE EXPLICIT EXCEPTION FOR %s" % self.node
			k = SSHKnownHosts(); k.updateDirect(self.node); k.write(); del k
			ret = os.system(cmd)
			if ret != 0:
				print "FAILED TWICE"
				sys.exit(1)

		#cmd = "rsync -qv -az -e ssh %(monitordir)s/BootManager.py 
		# %(monitordir)s/ChainBoot.py %(user)s@%(hostname)s:/tmp/source" % args
		#print cmd; os.system(cmd)

		# KILL any already running servers.
		cmd = """ssh %(user)s@%(hostname)s """ + \
		     """'ps ax | grep Rpyc | grep -v grep | awk "{print \$1}" | xargs kill 2> /dev/null' """
		cmd = cmd % args
		if self.verbose: print cmd
		os.system(cmd)

		# START a new rpyc server.
		cmd = """ssh %(user)s@%(hostname)s "export PYTHONPATH=\$HOME; """ + \
			 """python Rpyc/Servers/forking_server.py &> server.log < /dev/null &" """ 
		cmd = cmd % args
		if self.verbose: print cmd
		os.system(cmd)

		# This was tricky to make synchronous.  The combination of ssh-clients-4.7p1, 
		# and the following options seems to work well.
		cmd = """ssh -o ExitOnForwardFailure=yes -o BatchMode=yes """ + \
		      """-o PermitLocalCommand=yes -o LocalCommand='echo "READY"' """ + \
		      """-o ConnectTimeout=120 """ + \
		      """-n -N -L %(port)s:localhost:18812 """ + \
		      """%(user)s@%(hostname)s"""
		cmd = cmd % args
		if self.verbose: print cmd
		self.command = Sopen(cmd, shell=True, stdout=subprocess.PIPE)
		ret = self.command.stdout.read(5)
		if 'READY' in ret:
			# We can return without delay.
			time.sleep(1)
			return

		if self.command.returncode is not None:
			print "Failed to establish tunnel!"
			raise Exception("SSH Tunnel exception : %s %s" % (self.node, self.command.returncode))

		raise Exception("Unknown SSH Tunnel Exception: still running, but did not report 'READY'")

	def __del__(self):
		if self.command:
			if self.verbose: print "Killing SSH session %s" % self.port
			self.command.kill()


def steps_to_list(steps):
	ret_list = []
	for (id,label) in steps:
		ret_list.append(label)
	return ret_list

def index_to_id(steps,index):
	if index < len(steps):
		return steps[index][0]
	else:
		return "done"

def reboot(hostname, config=None, forced_action=None):

	node = hostname
	print "Creating session for %s" % node
	# update known_hosts file (in case the node has rebooted since last run)
	if config and not config.quiet: print "...updating known_hosts ssh-rsa key for %s" % node
	k = SSHKnownHosts(); k.update(node); k.write(); del k

	if config == None:
		session = PlanetLabSession(node, False, False)
	else:
		session = PlanetLabSession(node, config.nosetup, config.verbose)
	conn = session.get_connection(config)

	if forced_action == "reboot":
		conn.restart_node('rins')
		return True

	boot_state = conn.get_boot_state()
	if boot_state == "boot":
		print "...Boot state of %s already completed : skipping..." % node
		return False
	elif boot_state == "unknown":
		print "...Unknown bootstate for %s : skipping..."% node
		return False
	else:
		pass

	if conn.bootmanager_running():
		print "...BootManager is currently running.  Skipping host %s" % node
		return False

	if config != None:
		if config.force:
			conn.restart_bootmanager(config.force)
			return True

	if config and not config.quiet: print "...downloading dmesg from %s" % node
	dmesg = conn.get_dmesg()
	child = fdpexpect.fdspawn(dmesg)

	sequence = []
	while True:
		steps = [
			('scsierror'  , 'SCSI error : <\d+ \d+ \d+ \d+> return code = 0x\d+'),
			('ioerror'    , 'end_request: I/O error, dev sd\w+, sector \d+'),
			('buffererror', 'Buffer I/O error on device dm-\d, logical block \d+'),
			('atareadyerror'   , 'ata\d+: status=0x\d+ { DriveReady SeekComplete Error }'),
			('atacorrecterror' , 'ata\d+: error=0x\d+ { UncorrectableError }'),
			('sdXerror'   , 'sd\w: Current: sense key: Medium Error'),
			('floppytimeout','floppy0: floppy timeout called'),
			('floppyerror',  'end_request: I/O error, dev fd\w+, sector \d+'),

			# floppy0: floppy timeout called
			# end_request: I/O error, dev fd0, sector 0

			#Buffer I/O error on device dm-2, logical block 8888896
			#ata1: status=0x51 { DriveReady SeekComplete Error }
			#ata1: error=0x40 { UncorrectableError }
			#SCSI error : <0 0 0 0> return code = 0x8000002
			#sda: Current: sense key: Medium Error
			#	Additional sense: Unrecovered read error - auto reallocate failed

			#SCSI error : <0 2 0 0> return code = 0x40001
			#end_request: I/O error, dev sda, sector 572489600
		]
		id = index_to_id(steps, child.expect( steps_to_list(steps) + [ pexpect.EOF ]))
		sequence.append(id)

		if id == "done":
			break

	s = Set(sequence)
	if config and not config.quiet: print "SET: ", s

	if len(s) > 1:
		print "...Potential drive errors on %s" % node
		if len(s) == 2 and 'floppyerror' in s:
			print "...Should investigate.  Continuing with node."
		else:
			print "...Should investigate.  Skipping node."
			return False

	print "...Downloading bm.log from %s" % node
	log = conn.get_bootmanager_log()
	child = fdpexpect.fdspawn(log)

	time.sleep(1)

	if config and not config.quiet: print "...Scanning bm.log for errors"
	action_id = "dbg"
	sequence = []
	while True:

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
			('implementerror', 'Implementation Error'),
			('readonlyfs'   , '[Errno 30] Read-only file system'),
			('noinstall'    , 'notinstalled'),
			('bziperror'    , 'bzip2: Data integrity error when decompressing.'),
			('noblockdev'   , "No block devices detected."),
			('hardwarefail' , 'Hardware requirements not met'),
			('chrootfail'   , 'Running chroot /tmp/mnt/sysimg'),
			('modulefail'   , 'Unable to get list of system modules'),
			('writeerror'   , 'write error: No space left on device'),
			('nonode'       , 'Failed to authenticate call: No such node'),
			('authfail'     , 'Failed to authenticate call: Call could not be authenticated'),
			('bootcheckfail'     , 'BootCheckAuthentication'),
			('bootupdatefail'   , 'BootUpdateNode'),
		]
		list = steps_to_list(steps)
		index = child.expect( list + [ pexpect.EOF ])
		id = index_to_id(steps,index)
		sequence.append(id)

		if id == "exception":
			if config and not config.quiet: print "...Found An Exception!!!"
		elif index == len(list):
			#print "Reached EOF"
			break
		
	s = "-".join(sequence)
	print "   FOUND SEQUENCE: ", s

	if s == "bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-done":
		if config and not config.quiet: print "...Restarting BootManager.py on %s "% node
		conn.restart_bootmanager('boot')
	elif s == "bminit-cfg-auth-bootcheckfail-authfail-exception-update-bootupdatefail-authfail-debug-done":
		if conn.compare_and_repair_nodekeys():
			# the keys either are in sync or were forced in sync.
			# so try to reboot the node again.
			conn.restart_bootmanager('boot')
		else:
			# there was some failure to synchronize the keys.
			print "...Unable to repair node keys on %s" % node
	elif s == "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-protoerror-debug-done" or \
		 s == "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-debug-done":
		conn.restart_bootmanager('boot')
	elif s == "bminit-cfg-auth-getplc-update-debug-done":
		conn.restart_bootmanager('boot')
	elif s == "bminit-cfg-auth-getplc-installinit-validate-exception-modulefail-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-update-installinit-validate-exception-modulefail-update-debug-done":
		conn.restart_bootmanager('rins')
	elif s == "bminit-cfg-auth-getplc-exception-protoerror-update-protoerror-debug-done":
		conn.restart_bootmanager('boot')
	elif s == "bminit-cfg-auth-protoerror-exception-update-debug-done":
		conn.restart_bootmanager('boot')
	elif s == "bminit-cfg-auth-getplc-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-update-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done":
		# reinstall b/c it is not installed.
		conn.restart_bootmanager('rins')
	elif s == "bminit-cfg-auth-getplc-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-update-installinit-validate-exception-noinstall-update-debug-done":

		conn.restart_bootmanager('rins')
	elif s == "bminit-cfg-auth-getplc-update-hardware-installinit-exception-bmexceptrmfail-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-hardware-installinit-exception-bmexceptrmfail-update-debug-done":
		conn.restart_node('rins')
	elif s == "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-implementerror-bootupdatefail-update-debug-done":
		conn.restart_node('rins')
	elif s == "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-readonlyfs-update-debug-done":
		conn.restart_node('rins')
	elif s == "bminit-cfg-auth-getplc-hardware-installinit-installdisk-bziperror-exception-update-debug-done":
		conn.restart_bootmanager('rins')
	elif s == "bminit-cfg-auth-getplc-update-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done":
		conn.restart_bootmanager('rins')
	elif s == "bminit-cfg-exception-nocfg-update-bootupdatefail-nonode-debug-done" or \
		 s == "bminit-cfg-exception-update-bootupdatefail-nonode-debug-done":
		conn.dump_plconf_file()
	elif s == "bminit-cfg-auth-getplc-update-hardware-exception-noblockdev-hardwarefail-update-debug-done" or \
	     s == "bminit-cfg-auth-getplc-hardware-exception-noblockdev-hardwarefail-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-update-hardware-noblockdev-exception-hardwarefail-update-debug-done":
		print "...NOTIFY OWNER TO UPDATE BOOTCD!!!"
		pass

	elif s == "bminit-cfg-auth-getplc-update-hardware-exception-hardwarefail-update-debug-done":
		# MAKE An ACTION record that this host has failed hardware.  May
		# require either an exception "/minhw" or other manual intervention.
		# Definitely need to send out some more EMAIL.
		print "...NOTIFY OWNER OF BROKEN HARDWARE!!!"
		pass

	elif s == "bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-exception-chrootfail-update-debug-done" or \
	     s == "bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-exception-chrootfail-update-debug-done" or \
	     s == "bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-installcfg-exception-chrootfail-update-debug-done" or \
		 s == "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-writeerror-exception-chrootfail-update-debug-done":
		conn.restart_node('rins')
		#conn.restart_bootmanager('rins')
		print "...Need to follow up on this one."

		## If the disk is full, just start over.
		#conn.restart_bootmanager('rins')
	elif s == "":
		pass

	else:
		print "   HOST %s" % hostname
		print "   UNKNOWN SEQUENCE: %s" % s
		pass

	return True
	

# MAIN -------------------------------------------------------------------

def main():
	from config import config
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(node=None, nodelist=None, child=False, nosetup=False, verbose=False, force=None, quiet=False)
	parser.add_option("", "--child", dest="child", action="store_true", 
						help="This is the child mode of this process.")
	parser.add_option("", "--force", dest="force", metavar="boot_state",
						help="Force a boot state passed to BootManager.py.")
	parser.add_option("", "--quiet", dest="quiet", action="store_true", 
						help="Extra quiet output messages.")
	parser.add_option("", "--verbose", dest="verbose", action="store_true", 
						help="Extra debug output messages.")
	parser.add_option("", "--nosetup", dest="nosetup", action="store_true", 
						help="Do not perform the orginary setup phase.")
	parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
						help="A single node name to try to bring out of debug mode.")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
						help="A list of nodes to bring out of debug mode.")
	config = config(parser)
	config.parse_args()

	if config.nodelist:
		nodes = config.getListFromFile(config.nodelist)
	elif config.node:
		nodes = [ config.node ]
	else:
		parser.print_help()
		sys.exit(1)

	for node in nodes:
		reboot(node, config)

if __name__ == "__main__":
	main()
