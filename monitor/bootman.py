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

from monitor.util.sshknownhosts import SSHKnownHosts
from monitor.Rpyc import SocketConnection, Async
from monitor.Rpyc.Utils import *

from monitor import getconf
from monitor import config
from monitor import const
from monitor.model import *
from monitor.common import email_exception, found_within
from monitor.database.info.model import *
from monitor.database.info.interface import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.wrapper.emailTxt import mailtxt
from monitor.nodeconfig import network_config_to_str

from pcucontrol.util import command as moncommands
from pcucontrol.util.command import Sopen
from pcucontrol.transports.ssh import pxssh as pxssh
from pcucontrol.transports.ssh import fdpexpect as fdpexpect
from pcucontrol.transports.ssh import pexpect as pexpect

api = plc.getAuthAPI()
fb = None

def bootmanager_log_name(hostname):
	t_stamp = time.strftime("%Y-%m-%d-%H:%M")
	base_filename = "%s-bm.%s.log" % (t_stamp, hostname)
	short_target_filename = os.path.join('history', base_filename)
	return short_target_filename

def bootmanager_log_action(hostname, short_log_path, logtype="bm.log"):
	try:
		node = FindbadNodeRecord.get_latest_by(hostname=hostname)
		loginbase = PlcSite.query.get(node.plc_node_stats['site_id']).plc_site_stats['login_base']
		err = ""
	except:
		loginbase = "unknown"
		err = traceback.format_exc()

	act = ActionRecord(loginbase=loginbase,
						hostname=hostname,
						action='log',
						action_type=logtype,
						log_path=short_log_path,
						error_string=err)
	return
	

class ExceptionDoubleSSHError(Exception): pass

class NodeConnection:
	def __init__(self, connection, node, config):
		print "init nodeconnection"
		self.node = node
		self.c = connection
		self.config = config

	def get_boot_state(self):
		print "get_boot_state(self)"
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
		t_stamp = time.strftime("%Y-%m-%d-%H:%M")
		self.c.modules.os.system("dmesg > /var/log/dmesg.bm.log")
		download(self.c, "/var/log/dmesg.bm.log", "%s/history/%s-dmesg.%s.log" % (config.MONITOR_BOOTMANAGER_LOG, t_stamp, self.node))
		os.system("cp %s/history/%s-dmesg.%s.log %s/dmesg.%s.log" % (config.MONITOR_BOOTMANAGER_LOG, t_stamp, self.node, config.MONITOR_BOOTMANAGER_LOG, self.node))
		log = open("%s/dmesg.%s.log" % (config.MONITOR_BOOTMANAGER_LOG, self.node), 'r')
		return log

	def get_bootmanager_log(self):
		bm_name = bootmanager_log_name(self.node)
		download(self.c, "/tmp/bm.log", "%s/%s" % (config.MONITOR_BOOTMANAGER_LOG, bm_name))
		#email_exception(self.node, "collected BM log for %s" % self.node)
		bootmanager_log_action(self.node, bm_name, "collected_bm.log")
		os.system("cp %s/%s %s/bm.%s.log" % (config.MONITOR_BOOTMANAGER_LOG, bm_name, config.MONITOR_BOOTMANAGER_LOG, self.node))
		log = open("%s/bm.%s.log" % (config.MONITOR_BOOTMANAGER_LOG, self.node), 'r')
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
		
	def fsck_repair_node(self):
		c = self.c
		self.c.modules.sys.path.append("/tmp/source/")
		self.c.modules.os.chdir('/tmp/source')
		# TODO: restart
		# TODO: set boot state to node's actually boot state.
		# could be 'boot' or 'safeboot'
		self.c.modules.os.chdir('/tmp/source')
		if self.c.modules.os.path.exists('/tmp/BM_RUNNING'):
			print "Running MANUAL FSCK already... try again soon."
		else:
			print "Running MANUAL fsck on %s" % self.node
			cmd = "( touch /tmp/BM_RUNNING ;  " + \
				  "  fsck -v -f -y /dev/planetlab/root &> out.fsck ; " + \
				  "  fsck -v -f -y /dev/planetlab/vservers >> out.fsck 2>&1 ; " + \
				  "  python ./BootManager.py %s &> server.log < /dev/null ; " + \
				  "  rm -f /tmp/BM_RUNNING " + \
				  ") &" 
			cmd = cmd % self.get_nodestate()
			self.c.modules.os.system(cmd)
		#self.restart_bootmanager('boot')	
		pass

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

	def get_nodestate(self):
		try:
			return api.GetNodes(self.node, ['boot_state'])[0]['boot_state']
		except:
			traceback.print_exc()
			# NOTE: use last cached value from plc
			fbnode = FindbadNodeRecord.get_latest_by(hostname=self.node).to_dict()
			return fbnode['plc_node_stats']['boot_state']


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
		try:
			print "SocketConnection(localhost, %s" % self.port
			sc = SocketConnection("localhost", self.port)
			print "NodeConnection(%s, %s)" % (sc, self.node)
			conn = NodeConnection(sc, self.node, config)
		except:
			# NOTE: try twice since this can sometimes fail the first time. If
			# 		it fails again, let it go.
			conn = NodeConnection(SocketConnection("localhost", self.port), self.node, config)
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
		#cmd = "rsync -vvv -az -e ssh %(monitordir)s/Rpyc/ %(user)s@%(hostname)s:Rpyc 2> /dev/null" % args
		cmd = """rsync -vvv -az -e "ssh -o BatchMode=yes" %(monitordir)s/Rpyc/ %(user)s@%(hostname)s:Rpyc""" % args
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
			print "trying: ", cmd
			print [ "%s=%s" % (a, os.environ[a]) for a in filter(lambda x: 'SSH' in x, os.environ.keys()) ]
			ret = localos.system(cmd, timeout)
			print ret
			if ret != 0:
				print "\tFAILED TWICE"
				#email_exception("%s rsync failed twice" % self.node)
				raise ExceptionDoubleSSHError("Failed twice trying to login with updated ssh host key")

		t1 = time.time()
		# KILL any already running servers.
		ssh = moncommands.SSH(args['user'], args['hostname'], ssh_port)
		(ov,ev) = ssh.run_noexcept2("""<<\EOF
            rm -f out.log
            echo "kill server" >> out.log
			netstat -ap | grep python | grep 18812 | awk '{print $7}' | awk -F / '{print $1}' | xargs kill
            ps ax | grep Rpyc | grep -v grep | awk '{print $1}' | xargs kill 2> /dev/null ; 
            echo "export" >> out.log
            export PYTHONPATH=$HOME  ;
            echo "start server" >> out.log
            python Rpyc/Servers/forking_server.py &> server.log &
            echo "done" >> out.log
EOF""")
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

		msg = "ERROR setting up session for %s" % self.hostname
		try:
			if config == None:
				self.session = PlanetLabSession(self.hostname, False, True)
			else:
				self.session = PlanetLabSession(self.hostname, config.nosetup, config.verbose)
		except ExceptionDoubleSSHError, e:
			print msg
			return False
		except Exception, e:
			traceback.print_exc()
			email_exception(msg)
			return False

		print "Getting connection: 1st try"
		try:
			conn = self.session.get_connection(config)
		except EOFError:
			# NOTE: sometimes the wait in setup_host() is not long enough.  
			# So, here we try to wait a little longer before giving up entirely.
			try:
				print "Getting connection: 2nd try"
				time.sleep(self.session.timeout*5)
				conn = self.session.get_connection(config)
			except EOFError:
				# failed twice... no need to report this really, it's just in a
				# weird state...
				print "Getting connection: failed"
				email_exception(self.hostname, "failed twice to get connection")
				return False
			except:
				traceback.print_exc()
				email_exception(self.hostname)
				return False
		print "Getting connection: ok"
		#print "trying to use conn before returning it."
		#print conn.c.modules.sys.path
		#print conn.c.modules.os.path.exists('/tmp/source')
		#time.sleep(1)

		#print "conn: %s" % conn
		return conn

	def getSequences(self):

		# NOTE: The DB is now the autoritative record for all BM sequences. 
		# 		An admin can introduce new patterns and actions without touching code.
		sequences = {}

		bms = BootmanSequenceRecord.query.all()
		for s in bms:
			sequences[s.sequence] = s.action
		
		return sequences

	def getDiskSteps(self):
		steps = [
			('scsierror'  , 'SCSI error : <\d+ \d+ \d+ \d+> return code = 0x\d+'),
			('ioerror'    , 'end_request: I/O error, dev sd\w+, sector \d+'),
			('ccisserror' , 'cciss: cmd \w+ has CHECK CONDITION'),

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
			('protoerror2'  , '500 Internal Server Error'),
			('protoerror'   , 'XML RPC protocol error'),
			('nodehostname' , 'Configured node hostname does not resolve'),
			('implementerror', 'Implementation Error'),
			('fsckabort'	, 'is mounted.  e2fsck: Cannot continue, aborting'),
			('fsckfail'		, 'Running e2fsck -v -p /dev/planetlab/root failed'),
			('fsckfail2'	, 'Running e2fsck -v -p /dev/planetlab/vservers failed'),
			('readonlyfs'   , '\[Errno 30\] Read-only file system'),
			('baddisk'      , "IOError: \[Errno 13\] Permission denied: '/tmp/mnt/sysimg//vservers/\w+/etc/hosts'"),
			('noinstall'    , 'notinstalled'),
			('bziperror'    , 'bzip2: Data integrity error when decompressing.'),
			('noblockdev'   , "No block devices detected."),
			('missingkernel', "missingkernel"),
			('dnserror'     , 'Name or service not known'),
			('noparseconfig', "Found configuration file plnode.txt on floppy, but was unable to parse it"),
			('noconfig'		, "Unable to find and read a node configuration file"),
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
			('authfail2'    , 'Authentication Failed'),
			('bootcheckfail'  , 'BootCheckAuthentication'),
			('bootupdatefail' , 'BootUpdateNode'),
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
	ret = restore_basic(sitehist, hostname, config, forced_action)
	session.flush()
	return ret

def restore_basic(sitehist, hostname, config=None, forced_action=None):

	# NOTE: Nothing works if the bootcd is REALLY old.
	#       So, this is the first step.

	bootman_action = "unknown"

	fbnode = FindbadNodeRecord.get_latest_by(hostname=hostname).to_dict()
	recent_actions = sitehist.getRecentActions(hostname=hostname)

	if fbnode['observed_category'] == "OLDBOOTCD":
		print "\t...Notify owner to update BootImage!!!"

		if not found_within(recent_actions, 'newbootcd_notice', 3.5):
			sitehist.sendMessage('newbootcd_notice', hostname=hostname)

			print "\tDisabling %s due to out-of-date BootImage" % hostname
			api.UpdateNode(hostname, {'boot_state' : 'disabled'})

		# NOTE: nothing else is possible.
		return "disabled"

	debugnode = DebugInterface(hostname)
	conn = debugnode.getConnection()
	if type(conn) == type(False): return "connect_failed"

	boot_state = conn.get_boot_state()
	if boot_state != "debug":
		print "... %s in %s state: skipping..." % (hostname , boot_state)
		return "skipped" #boot_state == "boot"

	if conn.bootmanager_running():
		print "...BootManager is currently running.  Skipping host %s" %hostname 
		return "skipped" # True

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

			if not found_within(recent_actions, 'baddisk_notice', 7):
				print "baddisk_notice not found recently"

				log=conn.get_dmesg().read()
				sitehist.sendMessage('baddisk_notice', hostname=hostname, log=log)
				return "skipping_baddisk"
			else:
				# NOTE: "" does not add a new action record
				return ""


	print "...Downloading bm.log from %s" %hostname 
	log = conn.get_bootmanager_log()
	bm_log_data = log.read() # get data
	log.seek(0)	# reset fd pointer for fdspawn
	child = fdpexpect.fdspawn(log)

	if hasattr(config, 'collect') and config.collect: return "collect"

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
		args['bmlog'] = bm_log_data
		args['viart'] = False
		args['saveact'] = True
		args['ccemail'] = True

		sitehist.sendMessage('unknownsequence_notice', **args)

		conn.restart_bootmanager('boot')

		bootman_action = "restart_bootmanager"

		# NOTE: Do not set the pflags value for this sequence if it's unknown.
		# This way, we can check it again after we've fixed it.
		flag_set = False

	else:
		bootman_action = sequences[s]

		if   sequences[s] == "restart_bootmanager_boot":
			print "...Restarting BootManager.py on %s "%hostname 
			conn.restart_bootmanager('boot')
		elif sequences[s] == "restart_bootmanager_rins":
			print "...Restarting BootManager.py on %s "%hostname 
			conn.restart_bootmanager('reinstall')
		elif sequences[s] == "restart_node_rins":
			conn.restart_node('reinstall')
		elif sequences[s] == "restart_node_boot":
			conn.restart_node('boot')
		elif sequences[s] == "fsck_repair":
			conn.fsck_repair_node()
		elif sequences[s] == "repair_node_keys":
			if conn.compare_and_repair_nodekeys():
				# the keys either are in sync or were forced in sync.
				# so try to start BM again.
				conn.restart_bootmanager(conn.get_nodestate())
			else:
				# there was some failure to synchronize the keys.
				print "...Unable to repair node keys on %s" %hostname 
				if not found_within(recent_actions, 'nodeconfig_notice', 3.5):
					args = {}
					args['hostname'] = hostname
					sitehist.sendMessage('nodeconfig_notice', **args)
					conn.dump_plconf_file()
				else:
					# NOTE: do not add a new action record
					return ""

		elif sequences[s] == "unknownsequence_notice":
			args = {}
			args['hostname'] = hostname
			args['sequence'] = s
			args['bmlog'] = bm_log_data
			args['viart'] = False
			args['saveact'] = True
			args['ccemail'] = True

			sitehist.sendMessage('unknownsequence_notice', **args)
			conn.restart_bootmanager('boot')

		elif sequences[s] == "nodeconfig_notice":

			if not found_within(recent_actions, 'nodeconfig_notice', 3.5):
				args = {}
				args['hostname'] = hostname
				sitehist.sendMessage('nodeconfig_notice', **args)
				conn.dump_plconf_file()
			else:
				# NOTE: do not add a new action record
				return ""

		elif sequences[s] == "nodenetwork_email":

			if not found_within(recent_actions, 'nodeconfig_notice', 3.5):
				args = {}
				args['hostname'] = hostname
				args['bmlog'] = bm_log_data
				sitehist.sendMessage('nodeconfig_notice', **args)
				conn.dump_plconf_file()
			else:
				# NOTE: do not add a new action record
				return ""

		elif sequences[s] == "noblockdevice_notice":

			if not found_within(recent_actions, 'noblockdevice_notice', 3.5):
				args = {}
				#args.update(getconf.getconf(hostname)) # NOTE: Generates boot images for the user:
				args['hostname'] = hostname
			
				sitehist.sendMessage('noblockdevice_notice', **args)
			else:
				# NOTE: do not add a new action record
				return ""

		elif sequences[s] == "baddisk_notice":
			# MAKE An ACTION record that this host has failed hardware.  May
			# require either an exception "/minhw" or other manual intervention.
			# Definitely need to send out some more EMAIL.
			# TODO: email notice of broken hardware
			if not found_within(recent_actions, 'baddisk_notice', 7):
				print "...NOTIFYING OWNERS OF BROKEN HARDWARE on %s!!!" % hostname
				args = {}
				args['hostname'] = hostname
				args['log'] = conn.get_dmesg().read()

				sitehist.sendMessage('baddisk_notice', **args)
				#conn.set_nodestate('disabled')
			else:
				# NOTE: do not add a new action record
				return ""

		elif sequences[s] == "minimalhardware_notice":
			if not found_within(recent_actions, 'minimalhardware_notice', 7):
				print "...NOTIFYING OWNERS OF MINIMAL HARDWARE FAILURE on %s!!!" % hostname
				args = {}
				args['hostname'] = hostname
				args['bmlog'] = bm_log_data
				sitehist.sendMessage('minimalhardware_notice', **args)
			else:
				# NOTE: do not add a new action record
				return ""

		elif sequences[s] == "baddns_notice":
			if not found_within(recent_actions, 'baddns_notice', 1):
				print "...NOTIFYING OWNERS OF DNS FAILURE on %s!!!" % hostname
				args = {}
				try:
					node = plccache.GetNodeByName(hostname)
					net = api.GetInterfaces(node['interface_ids'])[0]
				except:
					email_exception()
					print traceback.print_exc()
					# TODO: api error. skip email, b/c all info is not available,
					# flag_set will not be recorded.
					return "exception"
				nodenet_str = network_config_to_str(net)

				args['hostname'] = hostname
				args['network_config'] = nodenet_str
				args['interface_id'] = net['interface_id']

				sitehist.sendMessage('baddns_notice', **args)
			else:
				# NOTE: do not add a new action record
				return ""

	return bootman_action
	

if __name__ == "__main__":
	print "ERROR: Can not execute module as a command! Please use commands/%s.py" % os.path.splitext(__file__)[0]
