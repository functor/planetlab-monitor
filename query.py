#!/usr/bin/python

import csv
import sys
import os
import config
from glob import glob
import re
from cgi import parse_qs

import vxargs
from config import config
from optparse import OptionParser
from automate import *

parser = OptionParser()
parser.set_defaults(nodelist=None, 
				    outdir=None,
					querystr=None,
					simple=False,
					run=False,
					cmdfile=None,)

parser.add_option("", "--nodelist", dest="nodelist", metavar="filename",
					help="Read list of nodes from specified file")
parser.add_option("", "--outdir", dest="outdir", metavar="dirname",
					help="Name of directory to place output")
parser.add_option("", "--query", dest="querystr", metavar="QUERY",
					help="a simple query string: key=value")
parser.add_option("", "--simple", dest="simple", action="store_true",
					help="display simple output")

config = config(parser)
config.parse_args()


if config.outdir == None: 
	outdir="checkhosts"
else: 
	outdir=config.outdir

nodelist = None
if config.nodelist is not None:
	nodelist = config.getListFromFile(config.nodelist)

if config.querystr == None:
	queries = parse_qs("IP_SUBNET=127.0.0.1")
else:
	queries = parse_qs(config.querystr)
	#(key,query) = config.querystr.split("=")

# Create a file list based on the provide nodelist or a simple pattern for all
# files in the given 'outdir' directory
filelist = None
if nodelist is not None:
	filelist = []
	for node in nodelist:
		filelist.append("%s/%s.out" % (outdir,node))
else:
	filelist = glob("%s/*.out" % outdir)

for file in filelist:
	vals = csv_to_hash(csv.reader(open(file,'r')))
	hostname = file[len(outdir):-4]
	m = True
	for key in queries.keys():
		q = re.compile(queries[key][0])
		if key in vals and q.match(vals[key]):
			m=(m and True)
		else:
			m=(m and False)
			
	if m:
		if config.simple:
			print hostname, vals[key]
		else:
			print hostname, vals
