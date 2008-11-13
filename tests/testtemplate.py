#!/usr/bin/python

from monitor.database import FindbadNodeRecord, FindbadPCURecord
from template import *
from nodequery import *
from monitor import util
import sys


dc7800list = util.file.getListFromFile("dc7800.txt")

# get node info
# if membership satisfied
#     get pcu info
#     verify pcu constraint
#     verify node constraint

fbquery = FindbadNodeRecord.get_all_latest()
for noderec in fbquery:
	fbinfo = noderec.to_dict()
	member = verifyType(dc7800['membership'], fbinfo) 
	if not member: continue
		
	if pcu_in(fbinfo):
		fbpcuinfo  = FindbadPCURecord.get_latest_by(plc_pcuid=fbinfo['plc_node_stats']['pcu_ids'][0]).to_dict()
	else:
		fbpcuinfo = None
	fbinfo['pcuinfo'] = fbpcuinfo

	pcuok = verifyType(dc7800['pcu']['constraint'], fbpcuinfo) 
	nodeok = verifyType(dc7800['node']['constraint'], fbinfo)
	print "pcuok : ", pcuok, " nodeok: ", nodeok , " ", hostname
	continue
	sys.exit(1)

	if not pcuok and not nodeok:
		# donation_down_one
		pass
	elif not pcuok and nodeok:
		# donation_nopcu_one
		pass
	elif pcuok and not nodeok:
		# reboot
		pass
	elif pcuok and nodeok:
		# noop 
		pass

	if pcuok:
		print "PCU-OK ", 
	else:
		print "PCU-BAD",
	if nodeok:
		print "NODE-OK ",
	else:
		print "NODE-BAD",
	print " for %-45s" % hostname
	


