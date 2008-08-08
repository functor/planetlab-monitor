#!/usr/bin/python

import plc
api = plc.getAuthAPI()

import reboot

import time
from model import *

import parser as parsermodule

parser = parsermodule.getParser()
parser.set_defaults(node=None, rins=False, bootstate=None, endrecord=False)
parser.add_option("", "--backoff", dest="backoff", action="store_true",
					help="Back off all penalties applied to a site.")
parser.add_option("", "--rins", dest="rins", action="store_true",
					help="Back off all penalties applied to a site.")
parser.add_option("", "--bootstate", dest="bootstate", 
					help="set the bootstate for a node.")
parser = parsermodule.getParser(['defaults'], parser)
config = parsermodule.parse_args(parser)

for node in config.args:
	config.node = node

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
