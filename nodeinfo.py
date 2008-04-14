#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
fb = soltesz.dbLoad("findbad")
act_all = soltesz.dbLoad("act_all")

import reboot

import time
from model import *

from config import config
from optparse import OptionParser

parser = OptionParser()
parser.set_defaults(node=None, endrecord=False)
parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
					help="A single node name to add to the nodegroup")
parser.add_option("", "--endrecord", dest="endrecord", action="store_true",
					help="Force an end to the action record; to prompt Montior to start messaging again.")
config = config(parser)
config.parse_args()

def diff_time(timestamp):
	now = time.time()
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

def plc_print_nodeinfo(plcnode):
	url = "https://www.planet-lab.org/db/nodes/index.php?nodepattern="
	plcnode['url'] = url + plcnode['hostname']

	print "%(hostname)s %(url)s" % plcnode
	print "   Checked: %s" % time.ctime()

	print "\t boot_state |   created   |   updated   | last_contact"
	print "\t %10.10s | %11.11s | %11.11s | %12s" % \
		(plcnode['boot_state'], diff_time(plcnode['date_created']),
		 diff_time(plcnode['last_updated']), 
		 diff_time(plcnode['last_contact']))

def fb_print_nodeinfo(fbnode):
	print "   Checked: ",
	if 'checked' in fbnode:
		print "%11.11s " % diff_time(fbnode['checked'])
	else:
		print "Unknown"
	print "\t      state |  ssh  |  pcu  | bootcd | category | kernel"
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	fbnode['kernel'] = fbnode['kernel'].split()[2]
	print "\t %(state)10.10s | %(ssh)5.5s | %(pcu)5.5s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode

def act_print_nodeinfo(actnode, header):
	if header[0]:
		print "   Created: %11.11s" % diff_time(actnode['date_created'])
		print "   LastTime %11.11s" % diff_time(actnode['time'])
		print "\t      RT     | category | action          | msg"
		header[0] = False

	if 'rt' in actnode:
		print "\t %5.5s %5.5s | %8.8s | %15.15s | %s" % \
			(actnode['rt']['Status'], actnode['rt']['id'][7:],
			 actnode['category'], actnode['action'][0], 
			 actnode['msg_format'][:-1])
	else:
		if type(actnode['action']) == type([]):
			action = actnode['action'][0]
		else:
			action = actnode['action']
		if 'category' in actnode:
			category = actnode['category']
		else:
			category = "none"
			
		print "\t       %5.5s | %8.8s | %15.15s | %s" % \
			(actnode['ticket_id'],
			 category, action, 
			 actnode['msg_format'][:-1])

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

	if pcuinfo['portstatus']['22'] == "open":
		print "\t ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no %s@%s" % (pcuinfo['username'], reboot.pcu_name(pcuinfo))
	if pcuinfo['portstatus']['23'] == "open":
		print "\t telnet %s" % (reboot.pcu_name(pcuinfo))
	if pcuinfo['portstatus']['80'] == "open" or \
		pcuinfo['portstatus']['443'] == "open":
		print "\t http://%s" % (reboot.pcu_name(pcuinfo))
	if pcuinfo['portstatus']['443'] == "open":
		print "\t racadm.py -r %s -u %s -p '%s'" % (pcuinfo['ip'], pcuinfo['username'], pcuinfo['password'])
		print "\t cmdhttps/locfg.pl -s %s -f iloxml/Reset_Server.xml -u %s -p %s | grep MESSAGE" % \
			(reboot.pcu_name(pcuinfo), pcuinfo['username'], pcuinfo['password'])

for node in config.args:
	config.node = node

	plc_nodeinfo = api.GetNodes({'hostname': config.node}, None)[0]
	fb_nodeinfo  = fb['nodes'][config.node]['values']

	plc_print_nodeinfo(plc_nodeinfo)
	fb_print_nodeinfo(fb_nodeinfo)

	if fb_nodeinfo['pcu'] == "PCU":
		pcu = reboot.get_pcu_values(fb_nodeinfo['plcnode']['pcu_ids'][0])
		pcu_print_info(pcu, config.node)

	if config.node in act_all and len(act_all[config.node]) > 0:
		header = [True]

		if config.endrecord:
			a = Action(config.node, act_all[config.node][0])
			a.delField('rt')
			a.delField('second-mail-at-oneweek')
			a.delField('second-mail-at-twoweeks')
			a.delField('first-found')
			rec = a.get()
			rec['action'] = ["close_rt"]
			rec['category'] = "UNKNOWN"
			rec['stage'] = "monitor-end-record"
			rec['time'] = time.time() - 7*60*60*24
			act_all[config.node].insert(0,rec)

		for act_nodeinfo in act_all[config.node]:
			act_print_nodeinfo(act_nodeinfo, header)
	else: act_nodeinfo = None

