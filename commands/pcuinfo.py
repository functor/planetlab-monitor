#!/usr/bin/python

import database
import plc
import parser as parsermodule
import sys
from reboot import pcu_name, get_pcu_values

import sys

def print_dict(dict):
	for key in dict.keys():
		print "%30s : %s" % (key, dict[key])

parser = parsermodule.getParser()
parser.set_defaults(withpcu=False,
					refresh=False)
parser.add_option("-f", "--nodelist",dest="filename",default="", metavar="FILE",
				  help="Provide the input file for the downnode list")
parser.add_option("", "--refresh", action="store_true", dest="refresh",
					help="Refresh the cached values")

config = parsermodule.parse_args(parser)

if not config.run:
	k = config.__dict__.keys()
	k.sort()
	for o in k:
		print o, "=", config.__dict__[o]
	print "Add --run to actually perform the command"
	sys.exit(1)

pculist = plccache.l_pcus # database.if_cached_else_refresh(1, 
						  #	config.refresh, 
						  #	"pculist", 
						  #	lambda : plc.GetPCUs())
for pcu in pculist:
	#print pcu
	#sys.exit(1)
	if pcu['model'] == None:
		continue

	if True: # pcu['model'].find("APC AP79xx/Masterswitch") >= 0:
		host = pcu_name(pcu)
		values = get_pcu_values(pcu['pcu_id'])
		if 'portstatus' not in values:
			portstatus = ""
		else:
			if values['reboot'] == 0 or (not isinstance(values['reboot'],int) and values['reboot'].find("error") >= 0):
				portstatus = "22:%(22)s 23:%(23)s" % values['portstatus']
		if values['reboot'] == 0:
			print "%6d %20s %50s %s" % (pcu['pcu_id'], pcu['password'], "%s@%s" % (pcu['username'], host), portstatus)

#database.dbDump("pculist", pculist, 'php')
