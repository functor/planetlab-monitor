#!/usr/bin/python

import os
import sys
import string
import time
from monitor import database
from monitor.database.info.model import *
import getopt

def usage():
	print "blacklist.py --delete=<i>" 

def main():

	try:
		longopts = ["delete=", "help"]
		(opts, argv) = getopt.getopt(sys.argv[1:], "d:h", longopts)
	except getopt.GetoptError, err:
		print "Error: " + err.msg
		sys.exit(1)

	blacklist = BlacklistRecord.query.all()
	hostnames = [ h.hostname for h in blacklist ]

	for (opt, optval) in opts:
		if opt in ["-d", "--delete"]:
			i = optval
			bl = BlacklistRecord.get_by(hostname=i)
			bl.delete()
		else:
			usage()
			sys.exit(0)

	i_cnt = 0
	for i in blacklist:
		print i.hostname
		i_cnt += 1


	while 1:
		line = sys.stdin.readline()
		if not line:
			break
		line = line.strip()
		if line not in hostnames:
			bl = BlacklistRecord(hostname=line)
			bl.flush()
			i_cnt += 1

	session.flush()
	print "Total %d nodes in blacklist" % (i_cnt)
	
if __name__ == '__main__':
	import os
	#try:
	main()
	#except Exception, error:
	#	print "Exception %s" % error
	#	sys.exit(0)
