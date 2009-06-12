#!/usr/bin/python

from monitor.wrapper import plc
api = plc.getAuthAPI()

from monitor import database
import time
from datetime import datetime, timedelta
import calendar

import sys
import time
from monitor.model import *

from monitorstats import *


def main():
	from monitor import parser as parsermodule

	parser = parsermodule.getParser()
	parser.set_defaults(node=None, aggname='aggregatenm', archivedir='archive-pdb', field='nm', value='Y', fromtime=None, load=False, state='BOOT')
	parser.add_option("", "--node", dest="node", metavar="nodename.edu", 
						help="A single node name to add to the nodegroup")
	parser.add_option("", "--archivedir", dest="archivedir", metavar="filename",
						help="Pickle file aggregate output.")
	parser.add_option("", "--aggname", dest="aggname", metavar="filename",
						help="Pickle file aggregate output.")
	parser.add_option("", "--field", dest="field", metavar="key",
						help="Which record field to extract from all files.")
	parser.add_option("", "--value", dest="value", metavar="val",
						help="Which value to look for in field.")
	parser.add_option("", "--state", dest="state", metavar="key",
						help="Which boot state to accept.")
	parser.add_option("", "--load", action="store_true",
						help="load aggregatenm rather than recreate it.")
	parser.add_option("", "--fromtime", dest="fromtime", metavar="YYYY-MM-DD",
						help="Specify a starting date from which to begin the query.")
	config = parsermodule.parse_args(parser)

	archive = get_archive(config.archivedir)
	agg = {}

	if config.fromtime:
		begin = config.fromtime
	else:
		begin = "2008-09-28"

	d = datetime_fromstr(begin)
	tdelta = timedelta(1)
	verbose = 1

	if not config.load:
		while True:
			file = get_filefromglob(d, "production.findbad", config.archivedir)
			print archive.path
			fb = archive.load(file)
			try:
				print "nodes: ", len(fb['nodes'])
				state_count=0
				for node in fb['nodes']:
					fb_nodeinfo  = fb['nodes'][node]['values']
					time = d.strftime("%Y-%m-%d")

					if type(fb_nodeinfo) == type([]):
						continue

					if fb_nodeinfo['state'] != config.state:
						continue
					state_count += 1

					if node not in agg:
						agg[node] = { 'total' : 0, 'up' : 0}

					agg[node]['total'] += 1
					if fb_nodeinfo[config.field] == config.value:
						agg[node]['up'] += 1
				print "%s nodes in state %s" % ( state_count, config.state )

				del fb
				verbose = 0
			except SystemExit:
				sys.exit(1)
			except KeyboardInterrupt:
				sys.exit(1)
			except:
				import traceback; print traceback.print_exc()
				print d.strftime("%Y-%m-%d"), "No record"

			d = d + tdelta
			if d > datetime.now(): break
	else:
		agg = database.dbLoad(config.aggname)
	
	for node in agg:
		if agg[node]['total'] > 0:
			if agg[node]['up'] != agg[node]['total']:
				print "%s %s" %  (node, float(agg[node]['up']) / float(agg[node]['total']))

	database.dbDump(config.aggname, agg)

if __name__ == "__main__":
	main()
