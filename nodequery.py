#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
fb = soltesz.dbLoad("findbad")
from nodecommon import *

import time

from config import config
from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(node=None, category=None, nodelist=None)
parser.add_option("", "--category", dest="category", metavar="category", 
					help="List all nodes in the given category")
parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
					help="A list of nodes to bring out of debug mode.")
config = config(parser)
config.parse_args()

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


def fb_print_nodeinfo(fbnode, hostname):
	fbnode['hostname'] = hostname
	fbnode['checked'] = diff_time(fbnode['checked'])
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	if 'ERROR' in fbnode['category']:
		fbnode['kernel'] = ""
	else:
		fbnode['kernel'] = fbnode['kernel'].split()[2]
	#fbnode['pcu'] = color_pcu_state(fbnode)
	print "%(hostname)-39s | %(checked)11.11s | %(state)10.10s | %(ssh)5.5s | %(pcu)6.6s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode

if config.nodelist:
	nodelist = config.getListFromFile(config.nodelist)
else:
	nodelist = fb['nodes'].keys()


for node in nodelist:
	config.node = node

	if node not in fb['nodes']:
		continue

	fb_nodeinfo  = fb['nodes'][node]['values']

	if config.category and \
		'state' in fb_nodeinfo and \
		config.category == fb_nodeinfo['state']:

			fb_print_nodeinfo(fb_nodeinfo, node)
	elif 'state' in fb_nodeinfo:
		fb_print_nodeinfo(fb_nodeinfo, node)
	else:
		pass
		


