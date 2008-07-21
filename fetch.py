#!/usr/bin/python

import csv
import sys
import os
import config
from glob import glob

import vxargs
from config import config
from optparse import OptionParser
from automate import *

def build_vx_args(shell_cmd):
	ssh_options="-q -o UserKnownHostsFile=junkssh -o StrictHostKeyChecking=no"
	cmd="""ssh %s root@{} """  % ssh_options
	args = cmd.split()
	args.append(shell_cmd)
	return args

def vx_start(filelist,outdir,cmd, timeout=0):
	args = build_vx_args(cmd)
	vxargs.start(None, 20, filelist, outdir, False, args, timeout)

if __name__ == "__main__":
	parser = OptionParser()
	parser.set_defaults(nodelist=None, 
						node=None,
						outdir=None,
						querystr=None,
						timeout=0,
						simple=False,
						run=False,
						cmdfile=None,)

	parser.add_option("", "--nodelist", dest="nodelist", metavar="filename",
						help="Read list of nodes from specified file")
	parser.add_option("", "--node", dest="node", metavar="hostname",
						help="specify a single node name.")
	parser.add_option("", "--timeout", dest="timeout", metavar="seconds",
						help="Number of seconds to wait before timing out on host.")
	parser.add_option("", "--outdir", dest="outdir", metavar="dirname",
						help="Name of directory to place output")
	parser.add_option("", "--cmd", dest="cmdfile", metavar="filename",
						help="Name of file that contains a unix-to-csv command " + \
							 "to run on the hosts.")

	config = config(parser)
	config.parse_args()

	if config.outdir == None: 
		outdir="checkhosts"
	else: 
		outdir=config.outdir

	if not os.path.exists(outdir):
		os.system('mkdir -p %s' % outdir)

	if config.nodelist == None and config.node == None:
		filelist="nocomon.txt"
		filelist = vxargs.getListFromFile(open(filelist,'r'))
	elif os.path.exists(str(config.nodelist)) and os.path.isfile(config.nodelist):
		filelist = vxargs.getListFromFile(open(config.nodelist,'r'))
	elif os.path.exists(str(config.nodelist)) and os.path.isdir(config.nodelist):
		filelist = get_hostlist_from_dir(config.nodelist)
	elif config.node is not None:
		filelist = [(config.node, '')]
	else:
		# probably no such file.
		raise Exception("No such file %s" % config.nodelist)

	if config.cmdfile == None:
		f = open("command.txt",'r')
		cmd = f.read()
	else:
		f = open(config.cmdfile,'r')
		cmd = f.read()

	vx_start(filelist, outdir, cmd, int(config.timeout))
