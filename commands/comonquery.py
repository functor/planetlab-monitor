#!/usr/bin/python


import sys
from monitor import database
from monitor.common import *
from monitor.model import Record
import glob
import os
import traceback

import time
import re
import string

from monitor.wrapper import plc
api = plc.getAuthAPI()

from monitor.util import file
from monitor import config

from monitor.sources import comon

default_fields="name,resptime,sshstatus,date,uptime,lastcotop,cpuspeed,memsize,disksize"

class NoKeyException(Exception): pass

def daysdown_print_nodeinfo(co_nodeinfo, hostname):
	co_nodeinfo['hostname'] = hostname
	co_nodeinfo['daysdown'] = Record.getStrDaysDown(co_nodeinfo)
	co_nodeinfo['intdaysdown'] = Record.getDaysDown(co_nodeinfo)

	print "%(intdaysdown)5s %(hostname)-44s | %(state)10.10s | %(daysdown)s" % co_nodeinfo

def co_print_nodeinfo(co_nodeinfo, hostname, fields=None):
	
	# co_nodeinfo['bootstate'] : unknown pattern
	co_nodeinfo['name'] = hostname

	if 'uptime' in co_nodeinfo and co_nodeinfo['uptime'] != "null":
		co_nodeinfo['uptime'] = diff_time(time.time()-float(co_nodeinfo['uptime']))

	if 'date' in co_nodeinfo and co_nodeinfo['date'] != "null":
		co_nodeinfo['date'] = diff_time(float(co_nodeinfo['date']))

	if fields == default_fields.split(','):

		print "%(name)-40s %(sshstatus)5.5s %(resptime)6.6s %(lastcotop)6.6s %(uptime)s" % co_nodeinfo
	else:
		format = ""
		for f in fields:
			format += "%%(%s)s " % f
		print format % co_nodeinfo

def main():

	from monitor import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(node=None, 
				select=None, 
				list=None, 
				dns=False,
				listkeys=False,
				pcuselect=None, 
				nodelist=None, 
				daysdown=None, 
				fields=default_fields)
	parser.add_option("", "--daysdown", dest="daysdown", action="store_true",
						help="List the node state and days down...")

	parser.add_option("", "--select", dest="select", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--fields", dest="fields", metavar="key,list,...", 
						help="a list of keys to display for each entry.")
	parser.add_option("", "--list", dest="list", action="store_true", 
						help="Write only the hostnames as output.")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
						help="A list of nodes to bring out of debug mode.")
	parser.add_option("", "--listkeys", dest="listkeys", action="store_true",
						help="A list of nodes to bring out of debug mode.")

	parser.add_option("", "--dns", dest="dns", action="store_true",
						help="A convenience query for dns values")

	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)
	
	#if config.fromtime:
	#	fb = None
	#else:
	#	fb = None

	# lastcotop measures whether cotop is actually running.  this is a better
	# metric than sshstatus, or other values from CoMon

	COMON_COTOPURL= "http://comon.cs.princeton.edu/status/tabulator.cgi?" + \
					"table=table_nodeview&formatcsv"
	if config.dns:
		config.fields = "name,dns1udp,dns1tcp,dns2udp,dns2tcp"
		config.select = "dns1udp>0||dns1tcp>0||dns2udp>0||dns2tcp>0"

	if config.fields == "all":
		cotop_url = COMON_COTOPURL
	else:
		cotop_url = COMON_COTOPURL + "&dumpcols='%s'" % config.fields

	if config.select:
		cotop_url = cotop_url + "&select='%s'" % config.select

	if config.listkeys:
		cotop_url = COMON_COTOPURL + "&limit=1"

	cotop = comon.Comon()
	cohash = cotop.coget(cotop_url)

	if config.nodelist:
		nodelist = file.getListFromFile(config.nodelist)
	else:
		# NOTE: list of nodes should come from comon query.   
		nodelist = cohash.keys()

	print "%(name)-40s %(sshstatus)5.5s %(resptime)6.6s %(lastcotop)6.6s %(uptime)s" % {
					'name' : 'hostname', 
					'sshstatus' : 'sshstatus', 
					'resptime' : 'resptime', 
					'lastcotop' : 'lastcotop', 
					'uptime' : 'uptime'}
	for node in nodelist:
		config.node = node

		if node not in cohash: continue

		co_nodeinfo = cohash[node]

		if config.listkeys:
			print "Primary keys available in the comon object:"
			for key in co_nodeinfo.keys():
				print "\t",key
			sys.exit(0)
			
		if config.list:
			print node
		else:
			if config.daysdown:
				daysdown_print_nodeinfo(co_nodeinfo, node)
			else:
				fields = config.fields.split(",")
				co_print_nodeinfo(co_nodeinfo, node, fields)
		
if __name__ == "__main__":
	main()
