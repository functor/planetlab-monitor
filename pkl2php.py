#!/usr/bin/python

import soltesz
from config import config
from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(filename=None)
parser.add_option("-i", "--idb", dest="input", metavar="dbname", 
					help="Provide the input dbname to convert")
parser.add_option("-o", "--odb", dest="output", metavar="dbname", 
					help="Provide the output dbname to save to")
config = config(parser)
config.parse_args()

if config.input is None:
	print "please provide a pickle file to convert"
	import sys
	sys.exit(1)
if config.output is None:
	# just use the input name.
	config.output = config.input

data = soltesz.dbLoad(config.input)
soltesz.dbDump(config.output, data, 'php')
