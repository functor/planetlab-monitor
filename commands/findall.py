#!/usr/bin/python 

from monitor import parser as parsermodule
from findbad import main as findbad_main
from findbadpcu import main as findbadpcu_main
from sitebad import main as sitebad_main
from nodebad import main as nodebad_main
from pcubad import main as pcubad_main
from monitor.wrapper import plccache
from monitor.database.info.model import  *
from monitor.common import  *
import sys

if __name__ == '__main__':

	parser = parsermodule.getParser(['nodesets'])

	parser.set_defaults( increment=False, dbname="findbad", cachenodes=False, 
						force=False, pcuselect=None, pcuid=None, pcu=None, checkpcu=False)
	parser.add_option("", "--cachenodes", action="store_true",
						help="Cache node lookup from PLC")
	parser.add_option("", "--dbname", dest="dbname", metavar="FILE", 
						help="Specify the name of the database to which the information is saved")
	parser.add_option("-i", "--increment", action="store_true", dest="increment", 
						help="Increment round number to force refresh or retry")
	parser.add_option("", "--force", action="store_true", dest="force", 
						help="Force probe without incrementing global 'round'.")
	parser.add_option("", "--checkpcu", dest="checkpcu", action="store_true",
						help="whether to include PCUs in the site status")

	parser = parsermodule.getParser(['defaults'], parser)
	
	cfg = parsermodule.parse_args(parser)

	try:
		print "findbad"
		findbad_main()
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		print "findbadpcu"
		findbadpcu_main()
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		print "nodebad"
		nodebad_main()
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		print "pcubad"
		pcubad_main()
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		print "sitebad"
		sitebad_main()
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
	except Exception, err:
		import traceback
		email_exception()
		print traceback.print_exc()
		print "Exception: %s" % err
		print "Saving data... exitting."
		sys.exit(0)
