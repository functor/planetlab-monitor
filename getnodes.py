#!/usr/bin/python

import database
import plc
from optparse import OptionParser
import sys
from reboot import pcu_name, get_pcu_values

import sys
from config import config

parser = OptionParser()
parser.set_defaults(withpcu=False,
					refresh=False)
parser.add_option("", "--refresh", action="store_true", dest="refresh",
					help="Refresh the cached values")


config = config(parser)
config.parse_args()

if not config.run:
	k = config.__dict__.keys()
	k.sort()
	for o in k:
		print o, "=", config.__dict__[o]
	print "Add --run to actually perform the command"
	sys.exit(1)

nodelist = database.if_cached_else_refresh(1, 
							config.refresh, 
							"l_plcnodes", 
							lambda : plc.getNodes({'peer_id':None}, ['hostname']))
nodes = [n['hostname'] for n in nodelist]

for nodename in nodes:
	print nodename
