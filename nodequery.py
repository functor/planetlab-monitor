#!/usr/bin/python


import sys
from monitor import database
from monitor.common import *
from monitor.query import *
from monitor.model import Record
import glob
import os
import traceback

import time
import re
import string

from monitor.wrapper import plc
api = plc.getAuthAPI()

from monitor.database.info.model import HistoryNodeRecord, FindbadNodeRecord, FindbadPCURecord, session
from monitor.util import file as utilfile
from monitor import config


def daysdown_print_nodeinfo(fbnode, hostname):
	fbnode['hostname'] = hostname
	fbnode['daysdown'] = Record.getStrDaysDown(fbnode)
	fbnode['intdaysdown'] = Record.getDaysDown(fbnode)

	print "%(intdaysdown)5s %(hostname)-44s | %(state)10.10s | %(daysdown)s" % fbnode

def fb_print_nodeinfo(fbnode, hostname, fields=None):
	#fbnode['hostname'] = hostname
	#fbnode['checked'] = diff_time(fbnode['checked'])
	if fbnode['bootcd_version']:
		fbnode['bootcd_version'] = fbnode['bootcd_version'].split()[-1]
	else:
		fbnode['bootcd_version'] = "unknown"
        if not fbnode['boot_server']:
                fbnode['boot_server'] = "unknown"
        if not fbnode['install_date']:
                fbnode['install_date'] = "unknown"
	fbnode['pcu'] = color_pcu_state(fbnode)

	if not fields:
		if ( fbnode['observed_status'] is not None and \
		   'DOWN' in fbnode['observed_status'] ) or \
		   fbnode['kernel_version'] is None:
			fbnode['kernel_version'] = ""
		else:
			fbnode['kernel_version'] = fbnode['kernel_version'].split()[2]

		if fbnode['plc_node_stats'] is not None:
			fbnode['boot_state'] = fbnode['plc_node_stats']['boot_state']
		else:
			fbnode['boot_state'] = "unknown"

		try:
			if len(fbnode['nodegroups']) > 0:
				fbnode['category'] = fbnode['nodegroups'][0]
		except:
			#print "ERROR!!!!!!!!!!!!!!!!!!!!!"
			pass

		print "%(hostname)-45s | %(date_checked)11.11s | %(boot_state)5.5s| %(observed_status)8.8s | %(ssh_status)5.5s | %(pcu)6.6s | %(bootcd_version)6.6s | %(boot_server)s | %(install_date)s | %(kernel_version)s" % fbnode
	else:
		format = ""
		for f in fields:
			format += "%%(%s)s " % f
		print format % fbnode

def main():

	from monitor import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(node=None, fromtime=None, select=None, list=None, listkeys=False,
						pcuselect=None, nodelist=None, daysdown=None, fields=None)
	parser.add_option("", "--daysdown", dest="daysdown", action="store_true",
						help="List the node state and days down...")
	parser.add_option("", "--select", dest="select", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--fields", dest="fields", metavar="key,list,...", 
						help="a list of keys to display for each entry.")
	parser.add_option("", "--list", dest="list", action="store_true", 
						help="Write only the hostnames as output.")
	parser.add_option("", "--pcuselect", dest="pcuselect", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
						help="A list of nodes to bring out of debug mode.")
	parser.add_option("", "--listkeys", dest="listkeys", action="store_true",
						help="A list of nodes to bring out of debug mode.")
	parser.add_option("", "--fromtime", dest="fromtime", metavar="YYYY-MM-DD",
					help="Specify a starting date from which to begin the query.")

	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)
	
	if config.fromtime:
		path = "archive-pdb"
		archive = database.SPickle(path)
		d = datetime_fromstr(config.fromtime)
		glob_str = "%s*.production.findbad.pkl" % d.strftime("%Y-%m-%d")
		os.chdir(path)
		#print glob_str
		file = glob.glob(glob_str)[0]
		#print "loading %s" % file
		os.chdir("..")
		fb = archive.load(file[:-4])
	else:
		#fbnodes = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname, orderBy='date_checked',distinct=True).reversed()
		fb = None

	if config.nodelist:
		nodelist = utilfile.getListFromFile(config.nodelist)
	else:
		# NOTE: list of nodes should come from findbad db.   Otherwise, we
		# don't know for sure that there's a record in the db..
		fbquery = HistoryNodeRecord.query.all()
		nodelist = [ n.hostname for n in fbquery ]

	pculist = None
	if config.select is not None and config.pcuselect is not None:
		nodelist = node_select(config.select, nodelist, fb)
		nodelist, pculist = pcu_select(config.pcuselect, nodelist)
	elif config.select is not None:
		nodelist = node_select(config.select, nodelist, fb)
	elif config.pcuselect is not None:
		print "thirhd node select"
		nodelist, pculist = pcu_select(config.pcuselect, nodelist)

	#if pculist:
	#	for pcu in pculist:
	#		print pcu

	print "len: %s" % len(nodelist)
	for node in nodelist:
		config.node = node

		try:
			# Find the most recent record
			fb_noderec = FindbadNodeRecord.get_latest_by(hostname=node) 
			if not fb_noderec: continue
			fb_nodeinfo = fb_noderec.to_dict()
		except KeyboardInterrupt:
			print "Exiting at user request: Ctrl-C"
			sys.exit(1)
		except:
			print traceback.print_exc()
			continue

		if config.listkeys:
			print "Primary keys available in the findbad object:"
			for key in fb_nodeinfo.keys():
				print "\t",key
			sys.exit(0)
			

		if config.list:
			print node
		else:
			if config.daysdown:
				daysdown_print_nodeinfo(fb_nodeinfo, node)
			else:
				if config.select:
					if config.fields:
						fields = config.fields.split(",")
					else:
						fields = None

					fb_print_nodeinfo(fb_nodeinfo, node, fields)
				elif not config.select and 'observed_status' in fb_nodeinfo:
					fb_print_nodeinfo(fb_nodeinfo, node)
				else:
					print "passing..."
					pass
		
if __name__ == "__main__":
	main()
