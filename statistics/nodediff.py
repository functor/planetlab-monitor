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
	del fb
	return nodelist

def print_nodelist(nodelist, file):
	for node in nodelist:
		if file:
			print >>file, node
		else:
			print node
	
def main():
	parser = parsermodule.getParser()
	parser.set_defaults(archivedir='archive-pdb', begin=None, end=None, 
						sequential=False, printnodes=False, select=None)

	parser.add_option("", "--archivedir", dest="archivedir", metavar="filename",
						help="Pickle file aggregate output.")
	parser.add_option("", "--select", dest="select", metavar="key",
						help="Select .")
	parser.add_option("", "--sequential", dest="sequential", action="store_true",
						help="Compare EVERY timestep between begin and end .")
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
	d_s2 = datetime_fromstr(config.begin) + tdelta
	d_end = datetime_fromstr(config.end)

	print d_s1
	print d_s2
	print d_end

	file_list = []
		# then the iterations are day-based.
	while d_end > d_s2:
		f_s1 = get_filefromglob(d_s1, "production.findbad", config.archivedir, True)
		if not config.sequential:
			file_list.append(f_s1)
		else:
			file_list += f_s1
			
		d_s1 = d_s2
		d_s2 = d_s1 + tdelta
		
	print file_list
	file_list = file_list[4:]

	xaxis = get_xaxis(file_list)

	data = []
	f_s1 = None
	f_s2 = None
	i = 0
	for file in file_list:

		i+=1
		f_s2 = file
		if f_s1 is None:
			f_s1 = f_s2
			continue

		s1 = set(nodes_from_time(archive, f_s1))
		s2 = set(nodes_from_time(archive, f_s2))

		print f_s1
		print "[ %s, %s, %s ]," % ( len(s2), len(s2-s1), len(s1-s2) )
		data.append( [ len(s2), len(s2-s1), len(s1-s2)] )

		print "%s nodes up" % len(s2-s1)
		print "Nodes s2 minus s1: len(s2-s1) = %s" % len(s2-s1)
		f_up = None
		f_down = None

		if config.printnodes:
			print_nodelist(s2-s1, f_up)

		print ""
		print "%s nodes down" % len(s1-s2)
		print "Nodes s1 minus s2: len(s1-s2) = %s" % len(s1-s2)

		if config.printnodes:
			print_nodelist(s1-s2, f_down)

		f_s1 = f_s2
		f_s2 = None

	print_graph(data, config.begin, config.end, xaxis)
# takes two arguments as dates, comparing the number of up nodes from one and
# the other.

if __name__ == "__main__":
	main()
