#!/usr/bin/python

import time, datetime
import os
import sys

start = datetime.datetime(int(sys.argv[1]),int(sys.argv[2]), int(sys.argv[3]))
#end = datetime.datetime(2010,06,10)
end = datetime.datetime(2004,08,31)

while start < end:
	file = "dump_comon_%s.bz2" % ( start.strftime("%Y%m%d") )
	cmd = "scp -q soltesz@opus:/n/fs/codeenlogs/comon_dumps/%s/%s ./" % (start.year, file)
	os.system(cmd)

	start += datetime.timedelta(1)

	try:
		os.stat(file)
		cmd = "./comon_summary_parser.py %s" % file
		os.system(cmd)
		os.remove(file)
	except OSError:
		continue
		

