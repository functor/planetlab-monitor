#!/usr/bin/python

import database 
import parser as parsermodule

parser = parsermodule.getParser()
parser.set_defaults(filename=None)
parser.add_option("-i", "--idb", dest="input", metavar="dbname", 
					help="Provide the input dbname to convert")
parser.add_option("-o", "--odb", dest="output", metavar="dbname", 
					help="Provide the output dbname to save to")
config = parsermodule.parse_args(parser)

if config.input is None:
	print "please provide a pickle file to convert"
	import sys
	sys.exit(1)
if config.output is None:
	# just use the input name.
	config.output = config.input

data = database.dbLoad(config.input)
database.dbDump(config.output, data, 'php')
