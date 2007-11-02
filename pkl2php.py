#!/usr/bin/python

import soltesz
from config import config
from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(filename=None)
parser.add_option("-f", "--dbname", dest="dbname", metavar="FILE", 
					help="Provide the input file to convert")
config = config(parser)
config.parse_args()

if config.dbname is None:
	print "please provide a pickle file to convert"
	import sys
	sys.exit(1)

data = soltesz.dbLoad(config.dbname)
soltesz.dbDump(config.dbname, data, 'php')
