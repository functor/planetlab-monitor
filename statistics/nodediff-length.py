#!/usr/bin/python


from monitor import config
from monitor.wrapper import plc
from monitor import parser as parsermodule
from monitor.model import *
from monitorstats import *
from monitor import database

import sys
import time
import calendar
from datetime import datetime, timedelta

from nodequeryold import verify,query_to_dict,node_select

api = plc.getAuthAPI()

def nodes_from_time(arch, file):
	fb = arch.load(file)

	nodelist = fb['nodes'].keys()
	nodelist = node_select(config.select, nodelist, fb)
	return nodelist

def print_nodelist(nodelist, file):
	for node in nodelist:
		if file:
			print >>file, node
		else:
			print node
	

def main():
	parser = parsermodule.getParser()
	parser.set_defaults(archivedir='archive-pdb', begin=None, end=None, printnodes=False, select=None)
	parser.add_option("", "--archivedir", dest="archivedir", metavar="filename",
						help="Pickle file aggregate output.")
	parser.add_option("", "--select", dest="select", metavar="key",
						help="Select .")
	parser.add_option("", "--print", dest="printnodes", action="store_true",
						help="print the nodes that have come up or down.")
	parser.add_option("", "--begin", dest="begin", metavar="YYYY-MM-DD",
						help="Specify a starting date from which to begin the query.")
	parser.add_option("", "--end", dest="end", metavar="YYYY-MM-DD",
						help="Specify a ending date at which queries end.")
	config = parsermodule.parse_args(parser)
	archive = get_archive(config.archivedir)

	if not config.begin or not config.end:
		print parsermodule.usage(parser)
		sys.exit(1)

	tdelta = timedelta(1)
	d_s1 = datetime_fromstr(config.begin)
	d_s2 = datetime_fromstr(config.end)
	d_end = d_s2

	print d_s1
	print d_s2
	print d_end

	data = []
	while d_end >= d_s2:

		f_s1 = get_filefromglob(d_s1, "production.findbad", config.archivedir)
		f_s2 = get_filefromglob(d_s2, "production.findbad", config.archivedir)

		s1 = set(nodes_from_time(archive, f_s1))
		s2 = set(nodes_from_time(archive, f_s2))

		print "[ %s, %s, %s ]," % ( len(s2), len(s2-s1), len(s1-s2) )
		data.append( [ len(s2), len(s2-s1), len(s1-s2)] )

		#print "len s2 : ", len(s2)
		#print "len s1 : ", len(s1)
		timestr = d_s2.strftime("%Y-%m-%d")
		if not config.printnodes:
			f_up = open("up-%s" % timestr, 'w')
			f_down = open("dn-%s" % timestr, 'w')
		else:
			print "%s nodes up" % len(s2-s1)
			print "Nodes s2 minus s1: len(s2-s1) = %s" % len(s2-s1)
			f_up = None
			f_down = None

		print_nodelist(s2-s1, f_up)

		if config.printnodes:
			print ""
			print "%s nodes down" % len(s1-s2)
			print "Nodes s1 minus s2: len(s1-s2) = %s" % len(s1-s2)

		print_nodelist(s1-s2, f_down)
		if not config.printnodes:
			f_up.close()
			f_down.close()

		d_s1 = d_s2
		d_s2 = d_s1 + tdelta
	
# takes two arguments as dates, comparing the number of up nodes from one and
# the other.

if __name__ == "__main__":
	main()
