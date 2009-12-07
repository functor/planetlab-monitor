#!/usr/bin/python

import os
import sys
import string
import time
from monitor import common
from monitor import database
from monitor.database.info.model import *
import getopt

def usage():
	print "blacklist.py --delete=<i>" 

def main():
	from monitor import parser as parsermodule
	parser = parsermodule.getParser(['nodesets'])

	parser.set_defaults( expires=0, delete=False, add=False, list=True, loginbase=False)
	parser.add_option("", "--expires", dest="expires", 
						help="Set expiration time for blacklisted objects (in seconds)" )
	parser.add_option("", "--delete", dest="delete", action="store_true",
						help="Remove objects from blacklist" )
	parser.add_option("", "--list", dest="list", action="store_true",
						help="List objects in blacklist" )
	parser.add_option("", "--add", dest="add", action="store_true",
						help="List objects in blacklist" )
	parser.add_option("", "--loginbase", dest="loginbase", action="store_true",
						help="List objects in blacklist" )

	config = parsermodule.parse_args(parser)

	l_nodes = common.get_nodeset(config)
	if config.site is None:
		loginbase = False
		if config.loginbase: loginbase=True
	else:
		loginbase = True
		print "Blacklisting site:", config.site


	hostnames_q = BlacklistRecord.getHostnameBlacklist()
	loginbases_q = BlacklistRecord.getLoginbaseBlacklist()
	hostnames  = [ h.hostname for h in hostnames_q ]
	loginbases = [ h.loginbase for h in loginbases_q ]
	hostnames_exp  = [ (h.hostname,h.date_created+timedelta(0,h.expires),h.date_created+timedelta(0,h.expires) < datetime.now() and h.expires != 0) for h in hostnames_q ]
	#loginbases_exp = [ (h.loginbase,h.date_created+timedelta(0,h.expires)) for h in loginbases_q ]
	loginbases_exp = [ (h.loginbase,h.date_created+timedelta(0,h.expires),h.date_created+timedelta(0,h.expires) < datetime.now() and h.expires != 0) for h in loginbases_q ]

	if config.add:
		print "Blacklisting nodes: ", l_nodes
		for host in l_nodes:
			if host not in hostnames:
				print "adding to blacklist %s" % host
				bl = BlacklistRecord(hostname=host, expires=int(config.expires))
				bl.flush()

		if loginbase:
			print "Blacklisting site: ", config.site
			if config.site not in loginbases:
				print "adding to blacklist %s" % config.site
				bl = BlacklistRecord(loginbase=config.site, expires=int(config.expires))
				bl.flush()

	elif config.delete:
		print "Deleting nodes: %s" % l_nodes
		for h in l_nodes:
			bl = BlacklistRecord.get_by(hostname=h)
			if bl: bl.delete()
		if config.site:
			print "Deleting site: %s" % config.site
			bl = BlacklistRecord.get_by(loginbase=config.site)
			if bl: bl.delete()
	else:
		# default option is to list
		if loginbase:
			objlist = loginbases_exp
		else:
			objlist = hostnames_exp

		for i in objlist:
			if i[2]:
				print i[0], i[1], "<-- expired"
			elif i[1] > datetime.now():
				print i[0], i[1]
			else:
				print i[0]
			
	session.flush()
	
if __name__ == '__main__':
	import os
	#try:
	main()
	#except Exception, error:
	#	print "Exception %s" % error
	#	sys.exit(0)
