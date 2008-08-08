#!/usr/bin/python

import sys
import database
import config
import parser as parsermodule

def nodes_from_time(time_str):
	path = "archive-pdb"
	archive = database.SPickle(path)
	d = datetime_fromstr(config.fromtime)
	glob_str = "%s*.production.findbad.pkl" % d.strftime("%Y-%m-%d")
	os.chdir(path)
	#print glob_str
	file = glob.glob(glob_str)[0]
	#print "loading %s" % file
	os.chdir("..")
	fb = archive.load(file[:-4])

	nodelist = fb['nodes'].keys()
	nodelist = node_select(config.select, nodelist, fb)
	

def main():
	parser = parsermodule.getParser()
	parser.set_defaults(nodeselect=None,)
	parser.add_option("", "--nodeselect", dest="nodeselect", metavar="state=BOOT", 
						help="""Query on the nodes to count""")

	parser = parsermodule.getParser(['defaults'], parser)
	cfg = parsermodule.parse_args(parser)

	time1 = config.args[0]
	time2 = config.args[1]

	s1 = nodes_from_time(time1)
	s2 = nodes_from_time(time2)

# takes two arguments as dates, comparing the number of up nodes from one and
# the other.
