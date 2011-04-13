#!/usr/bin/python

# Attempt to reboot a node in debug state.



import os
import sys
import time
import random
import signal
import traceback
import subprocess
from sets import Set
from monitor.bootman import *
from monitor.util import file 

# MAIN -------------------------------------------------------------------

def main():
	from monitor import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(child=False, collect=False, nosetup=False, verbose=False, 
						force=None, quiet=False)
	parser.add_option("", "--child", dest="child", action="store_true", 
						help="This is the child mode of this process.")
	parser.add_option("", "--force", dest="force", metavar="boot_state",
						help="Force a boot state passed to BootManager.py.")
	parser.add_option("", "--quiet", dest="quiet", action="store_true", 
						help="Extra quiet output messages.")
	parser.add_option("", "--verbose", dest="verbose", action="store_true", 
						help="Extra debug output messages.")
	parser.add_option("", "--nonet", dest="nonet", action="store_true", 
						help="Do not setup the network, use existing log files to re-run a test pass.")
	parser.add_option("", "--collect", dest="collect", action="store_true", 
						help="No action, just collect dmesg, and bm.log")
	parser.add_option("", "--nosetup", dest="nosetup", action="store_true", 
						help="Do not perform the orginary setup phase.")

	parser = parsermodule.getParser(['nodesets', 'defaults'], parser)
	config = parsermodule.parse_args(parser)

	if config.nodelist:
		nodes = file.getListFromFile(config.nodelist)
	elif config.node:
		nodes = [ config.node ]
	else:
		parser.print_help()
		sys.exit(1)

	for node in nodes:
		# get sitehist
		lb = plccache.plcdb_hn2lb[node]
		sitehist = SiteInterface.get_or_make(loginbase=lb)
		#reboot(node, config)
		restore(sitehist, node, config=None, forced_action=None)

if __name__ == "__main__":
	main()
