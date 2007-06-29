#!/usr/bin/python

import os
import sys
import string
import time
import soltesz
import plc
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

	l_blacklist = soltesz.if_cached_else(1, "l_blacklist", lambda : [])

	for (opt, optval) in opts:
		if opt in ["-d", "--delete"]:
			i = int(optval)
			del l_blacklist[i]
		else:
			usage()
			sys.exit(0)

	i_cnt = 0
	for i in l_blacklist:
		print i_cnt, " ", i
		i_cnt += 1

	while 1:
		line = sys.stdin.readline()
		if not line:
			break
		line = line.strip()
		if not line in l_blacklist:
			l_blacklist.append(line)

	print "Total %d nodes in blacklist" % (len(l_blacklist))
	soltesz.dbDump("l_blacklist")
	
if __name__ == '__main__':
	import os
	#try:
	main()
	#except Exception, error:
	#	print "Exception %s" % error
	#	sys.exit(0)
