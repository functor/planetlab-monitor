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

from monitor import config
from monitor.wrapper import plc

from pcucontrol.util import command
from pcucontrol.reboot import pcu_name, model_to_object, reboot_api, convert_oldmodelname_to_newmodelname, reboot_test_new


# Event class ID from pcu events
#NODE_POWER_CONTROL = 3

# Monitor user ID
#MONITOR_USER_ID = 11142

import logging
logger = logging.getLogger("monitor")
verbose = 1
#dryrun = 0;

def get_pcu_values(pcu_id):
	from monitor.database.info.model import FindbadPCURecord
	print "pcuid: %s" % pcu_id
	try:
		pcurec = FindbadPCURecord.get_latest_by(plc_pcuid=pcu_id)
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
		return "%s has no pcu" % nodename

	values = get_pcu_values(pcu['pcu_id'])
	if values == None:
		logger.debug("No values for pcu probe %s" % nodename)
		print "No values for pcu probe %s" % nodename
		return "no info for pcu_id %s" % pcu['pcu_id']
	
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
		from monitor.common import email_exception
		email_exception(node)
		print err

if __name__ == '__main__':
	logger = logging.getLogger("monitor")
	main()
	f = open("/tmp/rebootlog", 'a')
	f.write("reboot %s\n" % sys.argv)
	f.close()
