#!/usr/bin/python

import plc
api = plc.getAuthAPI()

import database
import reboot
import time
from datetime import datetime, timedelta
import calendar

import sys
import time
from monitor.model import *
from monitor.common import *

def get_filefromglob(d, str):
	import os
	import glob
	# TODO: This is aweful.
	path = "archive-pdb"
	archive = database.SPickle(path)
	glob_str = "%s*.%s.pkl" % (d.strftime("%Y-%m-%d"), str)
	os.chdir(path)
	#print glob_str
	#file = glob.glob(glob_str)[0]
	files = glob.glob(glob_str)
	#print "loading %s" % file
	os.chdir("..")
	files_chng = [ file[:-4] for file in files ]
	return files_chng
	#fb = archive.load(file[:-4])


def fb_print_nodeinfo(fbnode, verbose, date=None):
	if verbose: print "              state |  ssh  |  pcu  | bootcd | category | kernel"
	if 'checked' in fbnode:
		print "%11.11s " % diff_time(fbnode['checked']),
	else:
		if date: print date,
		else: print "Unknown",
		
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	fbnode['state'] = color_boot_state(get_current_state(fbnode))
	fbnode['boot_state'] = getvalue(fbnode, 'plcnode/boot_state')
	if len(fbnode['kernel'].split()) >= 3:
		fbnode['kernel'] = fbnode['kernel'].split()[2]
	print "    %(state)5s | %(boot_state)s | %(ssh)5.5s | %(pcu)5.5s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode

def pcu_print_info(pcuinfo, hostname):
	print "   Checked: ",
	if 'checked' in pcuinfo:
		print "%11.11s " % diff_time(pcuinfo['checked'])
	else:
		print "Unknown"

	print "\t            user   |          password | port | hostname "
	print "\t %17s | %17s | %4s | %30s | %s" % \
		(pcuinfo['username'], pcuinfo['password'], 
		 pcuinfo[hostname], reboot.pcu_name(pcuinfo), pcuinfo['model'])

	if 'portstatus' in pcuinfo and pcuinfo['portstatus'] != {}:
		if pcuinfo['portstatus']['22'] == "open":
			print "\t ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no %s@%s" % (pcuinfo['username'], reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['23'] == "open":
			print "\t telnet %s" % (reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['80'] == "open" or \
			pcuinfo['portstatus']['443'] == "open":
			print "\t http://%s" % (reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['443'] == "open":
			print "\t racadm.py -r %s -u %s -p '%s'" % (pcuinfo['ip'], pcuinfo['username'], pcuinfo['password'])
			print "\t cmdhttps/locfg.pl -s %s -f iloxml/Reset_Server.xml -u %s -p '%s' | grep MESSAGE" % \
				(reboot.pcu_name(pcuinfo), pcuinfo['username'], pcuinfo['password'])

def main():
	import parser as parsermodule

	parser = parsermodule.getParser()
	parser.set_defaults(node=None, fields='state', fromtime=None)
	parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
						help="A single node name to add to the nodegroup")
	parser.add_option("", "--fields", dest="fields", metavar="key",
						help="Which record field to extract from all files.")
	parser.add_option("", "--fromtime", dest="fromtime", metavar="YYYY-MM-DD",
						help="Specify a starting date from which to begin the query.")
	config = parsermodule.parse_args(parser)

	path = "archive-pdb"
	archive = database.SPickle(path)

	if config.fromtime:
		begin = config.fromtime
	else:
		begin = "2007-11-06"

	if config.node is None and len(config.args) > 0:
		config.node = config.args[0]
	elif config.node is None:
		print "Add a hostname to arguments"
		print "exit."
		sys.exit(1)

	d = datetime_fromstr(begin)
	tdelta = timedelta(1)
	verbose = 1

	while True:
		
		try:
			for file in get_filefromglob(d, "production.findbad"):
				#file = get_filefromglob(d, "production.findbad")
				#file = "%s.production.findbad" % d.strftime("%Y-%m-%d")
				fb = archive.load(file)
				if config.node in fb['nodes']:
					fb_nodeinfo  = fb['nodes'][config.node]['values']
					fb_print_nodeinfo(fb_nodeinfo, verbose, d.strftime("%Y-%m-%d"))

				del fb
				verbose = 0

		except KeyboardInterrupt:
			sys.exit(1)
		except:
			#import traceback; print traceback.print_exc()
			print d.strftime("%Y-%m-%d"), "No record"

		d = d + tdelta
		if d > datetime.now(): break

if __name__ == "__main__":
	main()
