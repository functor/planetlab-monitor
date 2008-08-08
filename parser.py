#!/usr/bin/python
import pickle
import os
import getopt
import sys
import __main__
from optparse import OptionParser
import config

def parse_bool(option, opt_str, value, parser):
	if opt_str in ["--debug"]:
		parser.values.debug = int(int(value))
	elif opt_str in ["--mail"]:
		parser.values.mail = int(int(value))
	elif opt_str in ["--bcc"]:
		parser.values.bcc = int(int(value))
	elif opt_str in ["--policysavedb"]:
		parser.values.policysavedb = int(int(value))
	elif opt_str in ["--squeeze"]:
		parser.values.squeeze = int(int(value))
	else:
		print "blue"

def parseSetDefaults(parser=None):
	if parser == None:
		parser = OptionParser()

	parser.set_defaults(debug = config.debug,
					mail = config.mail,
					bcc  = config.bcc,
					email = config.email,
					run = config.run,
					squeeze = config.squeeze,
					policysavedb = config.policysavedb)

	parser.add_option("", "--debug", dest="debug",
			  help="Enable debugging", 
			  type="int",
			  metavar="[0|1]",
			  action="callback", 
			  callback=parse_bool)
	parser.add_option("", "--mail", dest="mail",
			  help="Enable sending email",
			  type="int",
			  metavar="[0|1]",
			  action="callback", 
			  callback=parse_bool)
	parser.add_option("", "--bcc", dest="bcc",
			  help="Include BCC to user",
			  type="int",
			  metavar="[0|1]",
			  action="callback", 
			  callback=parse_bool)
	parser.add_option("", "--squeeze", dest="squeeze",
			  help="Squeeze sites or not",
			  type="int",
			  metavar="[0|1]",
			  action="callback", 
			  callback=parse_bool)
	parser.add_option("", "--policysavedb", dest="policysavedb",
			  help="Save the policy event database after a run",
			  type="int",
			  metavar="[0|1]",
			  action="callback", 
			  callback=parse_bool)
	parser.add_option("", "--run", dest="run", 
			  action="store_true",
			  help="Perform monitor or print configs")
	parser.add_option("", "--email", dest="email",
			  help="Specify an email address to use for mail when "+\
					"debug is enabled or for bcc when it is not")
	return parser

def parseSetNodeSets(parser=None):
	if parser == None:
		parser = OptionParser()
	
	parser.set_defaults(node=None, site=None, nodelist=None, nodeselect=False, nodegroup=None)
	parser.add_option("", "--node", dest="node", metavar="hostname", 
						help="Provide a single node to operate on")
	parser.add_option("", "--site", dest="site", metavar="site name",
						help="Specify a single site to operate on")
	parser.add_option("", "--nodegroup", dest="nodegroup", metavar="GroupName", 
						help="Provide the nodegroup for the list of nodes.")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="FILE", 
						help="Provide the input file for the list of objects")
	parser.add_option("", "--nodeselect", dest="nodeselect", metavar="query string", 
						help="Provide a selection string to return a node list.")
	return parser


def getParser(parsesets=[], parser=None):
	if parser == None:
		p = OptionParser()
	else:
		p = parser

	if 'nodesets' in parsesets:
		p = parseSetNodeSets(p)
	if 'defaults' in parsesets:
		p = parseSetDefaults(p)

	return p
	
def parse_args(parser):
	class obj: pass
	o = obj()
	(options, args) = parser.parse_args()
	o.__dict__.update(options.__dict__)
	o.__dict__['args'] = args
	config.updatemodule(config, o)
	return config

def print_values(parser):
	exclude = ['parser']
	for key in parser.__dict__.keys():
		if key not in exclude:
			print "%20s == %s" % (key, parser.__dict__[key])
	
def usage(parser):
	print_values(parser)
	parser.print_help()
