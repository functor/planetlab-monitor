#!/usr/bin/python 

from monitor import parser as parsermodule
from findbad import main as findbad_main
from findbadpcu import main as findbadpcu_main
from sitebad import main as sitebad_main
import sys

if __name__ == '__main__':

	parser = parsermodule.getParser(['nodesets'])

	parser.set_defaults( increment=False, dbname="findbad", cachenodes=False, 
						force=False,)
	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser.add_option("", "--force", action="store_true", dest="force", 
						help="Force probe without incrementing global 'round'.")

	parser = parsermodule.getParser(['defaults'], parser)
	
	cfg = parsermodule.parse_args(parser)

	try:
		findbad_main()
		findbadpcu_main()
		sitebad_main()
	except Exception, err:
		import traceback
		print traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
