#!/usr/bin/python

from monitor.wrapper import plc
api = plc.getAuthAPI()

from monitor import *
from monitor import util
from monitor import parser as parsermodule

from monitor.database.info.model import *
from monitor import reboot

import time
from monitor.model import *
from monitor.common import *
#from monitor.model import node_end_record, PersistFlags

parser = parsermodule.getParser()
parser.set_defaults(node=None, 
					findbad=False,
					endrecord=False)
parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
					help="A single node name to add to the nodegroup")
parser.add_option("", "--endrecord", dest="endrecord", action="store_true",
					help="Force an end to the action record; to prompt Montior to start messaging again.")
parser.add_option("", "--findbad", dest="findbad", action="store_true", 
					help="Re-run findbad on the nodes we're going to check before acting.")
parser.add_option("", "--bootcd", dest="bootcd", action="store_true",
					help="A stock help message for fetching a new BootCD from the PLC GUI.")
config = parsermodule.parse_args(parser)


def plc_print_nodeinfo(plcnode):
	url = "https://www.planet-lab.org/db/nodes/index.php?nodepattern="
	plcnode['url'] = url + plcnode['hostname']

	print "%(hostname)s %(url)s" % plcnode
	print "   Checked: %s" % time.ctime()

	print "\t boot_state |   created   |   updated   | last_contact | key"
	print "\t       %5s | %11.11s | %11.11s | %12s | %s" % \
		(color_boot_state(plcnode['boot_state']), diff_time(plcnode['date_created']),
		 diff_time(plcnode['last_updated']), 
		 diff_time(plcnode['last_contact']), plcnode['key'])

def fb_print_nodeinfo(fbnode):
	pf = PersistFlags(fbnode['hostname'], 1, db='node_persistflags')
	try:
		fbnode['last_change'] = diff_time(pf.last_changed)
	except:
		fbnode['last_change'] = diff_time(time.time())
	print "   Checked: ",
	if 'checked' in fbnode:
		print "%11.11s " % diff_time(fbnode['checked'])
	else:
		print "Unknown"
	print "\t      state |  ssh  |  pcu  | bootcd | category | last change | kernel"
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	if 'state' in fbnode:
		fbnode['state'] = color_boot_state(get_current_state(fbnode))
	else:
		fbnode['state'] = "none"
	if len(fbnode['kernel'].split()) > 2:
		fbnode['kernel'] = fbnode['kernel'].split()[2]
	print "\t       %(state)5s | %(ssh)5.5s | %(pcu)5.5s | %(bootcd)6.6s | %(category)8.8s | %(last_change)11s | %(kernel)s" % fbnode

def act_print_nodeinfo(actnode, header):
	if header[0]:
		if 'date_created' in actnode:
			print "   Created: %11.11s" % diff_time(actnode['date_created'])
		print "   LastTime %11.11s" % diff_time(actnode['time'])
		print "\t      RT     | category | action          | msg"
		header[0] = False

	if 'rt' in actnode and 'Status' in actnode['rt']:
		print "\t %5.5s %5.5s | %8.8s | %15.15s | %s" % \
			(actnode['rt']['Status'], actnode['rt']['id'][7:],
			 actnode['category'], actnode['action'][0], actnode['info'][1:])
	else:
		if type(actnode['action']) == type([]):
			action = actnode['action'][0]
		else:
			action = actnode['action']
		if 'category' in actnode:
			category = actnode['category']
		else:
			category = "none"
			
		if 'msg_format' in actnode:
			print "\t       %5.5s | %8.8s | %15.15s | %s" % \
			(actnode['ticket_id'],
			 category, action, 
			 actnode['msg_format'][:-1])
		else:
			print "\t       %5.5s | %8.8s | %15.15s" % \
			(actnode['ticket_id'],
			 category, action)

def pcu_print_info(pcuinfo, hostname):
	print "   Checked: ",
	if 'checked' in pcuinfo:
		print "%11.11s " % diff_time(pcuinfo['checked'])
	else:
		print "Unknown"

	print "\t            user   |          password | port | pcu_id | hostname "
	print "\t %17s | %17s | %4s | %6s | %30s | %s" % \
		(pcuinfo['username'], pcuinfo['password'], 
		 pcuinfo[hostname], pcuinfo['pcu_id'], reboot.pcu_name(pcuinfo), pcuinfo['model'])

	if 'portstatus' in pcuinfo and pcuinfo['portstatus'] != {} and pcuinfo['portstatus'] != None:
		if pcuinfo['portstatus']['22'] == "open":
			print "\t ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no %s@%s" % (pcuinfo['username'], reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['23'] == "open":
			print "\t telnet %s" % (reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['80'] == "open" or \
			pcuinfo['portstatus']['443'] == "open":
			print "\t https://%s" % (reboot.pcu_name(pcuinfo))
			print "\t import %s.png" % (reboot.pcu_name(pcuinfo))
			print """\t mutt -s "crash for %s" -a %s.png sapanb@cs.princeton.edu < /dev/null""" % (hostname, reboot.pcu_name(pcuinfo))
		if pcuinfo['portstatus']['443'] == "open":
			print "\t racadm.py -r %s -u %s -p '%s'" % (pcuinfo['ip'], pcuinfo['username'], pcuinfo['password'])
			print "\t cmdhttps/locfg.pl -s %s -f iloxml/Reset_Server.xml -u %s -p '%s' | grep MESSAGE" % \
				(reboot.pcu_name(pcuinfo), pcuinfo['username'], pcuinfo['password'])
			print "\t cmdhttps/locfg.pl -s %s -f iloxml/License.xml -u %s -p '%s' | grep MESSAGE" % \
				(reboot.pcu_name(pcuinfo), pcuinfo['username'], pcuinfo['password'])
		if pcuinfo['portstatus']['16992'] == "open":
			print "\t ./cmdamt/remoteControl -A -verbose 'http://%s:16992/RemoteControlService' -user admin -pass '%s'" % (reboot.pcu_name(pcuinfo), pcuinfo['password'])

if config.findbad:
	# rerun findbad with the nodes in the given nodes.
	import os
	file = "findbad.txt"
	util.file.setFileFromList(file, config.args)
	os.system("./findbad.py --cachenodes --debug=0 --dbname=findbad --increment --nodelist %s" % file)

for node in config.args:
	config.node = node

	plc_nodeinfo = api.GetNodes({'hostname': config.node}, None)[0]
	fb_noderec = FindbadNodeRecord.get_latest_by(hostname=node) 
	fb_nodeinfo = fb_noderec.to_dict()
	plc_print_nodeinfo(plc_nodeinfo)

	fb_nodeinfo['hostname'] = node
	fb_print_nodeinfo(fb_nodeinfo)

	if fb_nodeinfo['pcu'] == "PCU":
		pcu = reboot.get_pcu_values(fb_nodeinfo['plcnode']['pcu_ids'][0])
		if pcu: pcu_print_info(pcu, config.node)

	try:
		act_all = database.dbLoad("act_all")
	except:
		act_all = {}
	if config.node in act_all and len(act_all[config.node]) > 0:
		header = [True]

		if config.endrecord:
			node_end_record(config.node)
			#a = Action(config.node, act_all[config.node][0])
			#a.delField('rt')
			#a.delField('found_rt_ticket')
			#a.delField('second-mail-at-oneweek')
			#a.delField('second-mail-at-twoweeks')
			#a.delField('first-found')
			#rec = a.get()
			#rec['action'] = ["close_rt"]
			#rec['category'] = "UNKNOWN"
			#rec['stage'] = "monitor-end-record"
			#rec['time'] = time.time() - 7*60*60*24
			#act_all[config.node].insert(0,rec)
			#database.dbDump("act_all", act_all)

		for act_nodeinfo in act_all[config.node]:
			act_print_nodeinfo(act_nodeinfo, header)
	else: act_nodeinfo = None

	print ""

	if config.bootcd:
		print """
If you need a new bootcd, the steps are very simple:

Visit:
 * https://www.planet-lab.org/db/nodes/index.php?nodepattern=%s
 * Select Download -> Download ISO image for %s
 * Save the ISO, and burn it to a writable CD-ROM.
 * Replace the old CD and reboot the machine.

Please let me know if you have any additional questions.
""" % (config.node, config.node)

