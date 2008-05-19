#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
import reboot
import time
from datetime import datetime, timedelta
import calendar

import time
from model import *
from nodecommon import *

from config import config
from optparse import OptionParser

parser = OptionParser()
parser.set_defaults(node=None, fields='state', fromtime=None)
parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
					help="A single node name to add to the nodegroup")
parser.add_option("", "--fields", dest="fields", metavar="key",
					help="Which record field to extract from all files.")
parser.add_option("", "--fromtime", dest="fromtime", metavar="YYYY-MM-DD",
					help="Specify a starting date from which to begin the query.")
config = config(parser)
config.parse_args()

def datetime_fromstr(str):
    if '-' in str:
        tup = time.strptime(str, "%Y-%m-%d")
    elif '/' in str:
        tup = time.strptime(str, "%m/%d/%Y")
    else:
        tup = time.strptime(str, "%m/%d/%Y")
    return datetime.fromtimestamp(calendar.timegm(tup))

def diff_time(timestamp):
	now = time.time()
	if timestamp == None:
		return "unknown"
	diff = now - timestamp
	# return the number of seconds as a difference from current time.
	t_str = ""
	if diff < 60: # sec in min.
		t = diff
		t_str = "%s sec ago" % t
	elif diff < 60*60: # sec in hour
		t = diff // (60)
		t_str = "%s min ago" % int(t)
	elif diff < 60*60*24: # sec in day
		t = diff // (60*60)
		t_str = "%s hours ago" % int(t)
	elif diff < 60*60*24*7: # sec in week
		t = diff // (60*60*24)
		t_str = "%s days ago" % int(t)
	elif diff < 60*60*24*30: # approx sec in month
		t = diff // (60*60*24*7)
		t_str = "%s weeks ago" % int(t)
	elif diff > 60*60*24*30: # approx sec in month
		t = diff // (60*60*24*7*30)
		t_str = "%s months ago" % int(t)
	return t_str

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
	fbnode['kernel'] = fbnode['kernel'].split()[2]
	print "    %(state)5s | %(ssh)5.5s | %(pcu)5.5s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode

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

path = "archive-pdb"
archive = soltesz.SPickle(path)

if config.fromtime:
	begin = config.fromtime
else:
	begin = "2007-11-06"

d = datetime_fromstr(begin)
tdelta = timedelta(1)
verbose = 1

while True:
	file = "%s.production.findbad" % d.strftime("%Y-%m-%d")
	
	try:
		fb = archive.load(file)
		if config.node in fb['nodes']:
			fb_nodeinfo  = fb['nodes'][config.node]['values']
			fb_print_nodeinfo(fb_nodeinfo, verbose, d.strftime("%Y-%m-%d"))

		del fb
		verbose = 0
	except:
		print d.strftime("%Y-%m-%d"), "No record"

	d = d + tdelta
	if d > datetime.now(): break

