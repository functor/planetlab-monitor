#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
#fb = soltesz.dbLoad("findbad")
#act_all = soltesz.dbLoad("act_all")

import reboot

import time
from model import *

from config import config
from optparse import OptionParser

parser = OptionParser()
parser.set_defaults(node=None, rins=False, bootstate=None, endrecord=False)
parser.add_option("", "--backoff", dest="backoff", action="store_true",
					help="Back off all penalties applied to a site.")
parser.add_option("", "--rins", dest="rins", action="store_true",
					help="Back off all penalties applied to a site.")
parser.add_option("", "--bootstate", dest="bootstate", 
					help="set the bootstate for a node.")
config = config(parser)
config.parse_args()

for node in config.args:
	config.node = node

	#plc_nodeinfo = api.GetNodes({'hostname': config.node}, None)[0]
	#fb_nodeinfo  = fb['nodes'][config.node]['values']

	if config.bootstate:
		print "Setting %s to bootstate %s" % ( node, config.bootstate )
		api.UpdateNode(node, {'boot_state' : config.bootstate})

	if config.rins:
		print "Setting %s to rins" % node
		api.UpdateNode(node, {'boot_state' : 'rins'})

	if config.backoff:
		print "Enabling Slices & Slice Creation for %s" % node
		plc.enableSlices(node)
		plc.enableSliceCreation(node)

		# plc_print_nodeinfo(plc_nodeinfo)
		# fb_print_nodeinfo(fb_nodeinfo)
