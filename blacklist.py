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

	loginbase = False

	try:
		longopts = ["delete=", "loginbase", "help"]
		(opts, argv) = getopt.getopt(sys.argv[1:], "d:lh", longopts)
	except getopt.GetoptError, err:
		print "Error: " + err.msg
		sys.exit(1)

	hostnames_q = BlacklistRecord.getHostnameBlacklist()
	loginbases_q = BlacklistRecord.getLoginbaseBlacklist()
	hostnames  = [ h.hostname for h in hostnames_q ]
	loginbases = [ h.loginbase for h in loginbases_q ]

	for (opt, optval) in opts:
		if opt in ["-d", "--delete"]:
			i = optval
			bl = BlacklistRecord.get_by(hostname=i)
			bl.delete()
		elif opt in ["-l", "--loginbase"]:
			loginbase = True
		else:
			usage()
			sys.exit(0)

	i_cnt = 0
	if not loginbase:
		for i in hostnames:
			print i
			i_cnt += 1
	else:
		for i in loginbases:
			print i
			i_cnt += 1
		


	while 1:
		line = sys.stdin.readline()
		if not line:
			break
		line = line.strip()
		if line not in hostnames and line not in loginbases:
			if loginbase:
				bl = BlacklistRecord(loginbase=line)
			else:
				bl = BlacklistRecord(hostname=line)
			bl.flush()
			i_cnt += 1

	session.flush()
	if loginbase:
		print "Total %d loginbases in blacklist" % (i_cnt)
	else:
		print "Total %d nodes in blacklist" % (i_cnt)
	
if __name__ == '__main__':
	import os
	#try:
	main()
	#except Exception, error:
	#	print "Exception %s" % error
	#	sys.exit(0)
