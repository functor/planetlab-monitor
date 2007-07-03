#!/usr/bin/python
import pickle
import os
import getopt
import sys
import __main__

XMLRPC_SERVER="https://boot.planet-lab.org/PLCAPI/"

class config:
	debug = True
	mail = False
	bcc  = True
	email = "soltesz@cs.utk.edu"
	userlist = None
	cachert = True
	cachenodes = True
	cachesites = True
	squeeze = False
	policysavedb = True
	__file = ".config"

	def __init__(self):
		 if os.path.exists(self.__file): # file exists, read that.
		 	f = open(self.__file, 'r')
			o = pickle.load(f)
			self.__dict__.update(o)
			f.close()

	def getListFromFile(self, file):
		f = open(file, 'r')
		list = []
		for line in f:
			line = line.strip()
			list += [line]
		return list
		
	def save(self):
		f = open(self.__file, 'w')
		o = {'debug': self.debug, 
			 'mail': self.mail, 
			 'bcc': self.bcc, 
			 'email':self.email,
			 'userlist': self.userlist,
			 'cachert': self.cachert, 
			 'cachenodes' : self.cachenodes, 
			 'cachesites': self.cachesites,
			 'squeeze':self.squeeze,
			 'policysavedb':self.policysavedb}
		pickle.dump(o, f)
		f.close()


def usage():
	config = __main__.config()
     #   --cachesites=[0|1]      Cache Sites from PLC (current: %s)
     #	 --status                Print memory usage statistics and exit
	print """
Settings:
        --debug=[0|1]           Set debugging        (current: %s)
        --mail=[0|1]            Send mail or not     (current: %s)
        --bcc=[0|1]             Include bcc of user  (current: %s)
        --email=[email]         Email to use above   (current: %s)
        --userlist=[filename]   Use a list of nodes  (current: %s)
        --cachert=[0|1]      	Cache the RT db      (current: %s)
        --cachenodes=[0|1]      Cache Nodes from PLC (current: %s)
        --squeeze=[0|1]         Squeeze sites or not (current: %s)
        --policysavedb=[0|1]    Save policy DBs      (current: %s)
        -h, --help              This message
""".lstrip() % (config.debug, 
			    config.mail, 
				config.bcc, 
			    config.email, 
				config.userlist, 
				config.cachert, 
				config.cachenodes, 
				config.squeeze, 
				config.policysavedb)

def main():
	""" Start threads, do some housekeeping, then daemonize. """
	# Defaults
	config = __main__.config()

	try:
		longopts = [ "debug=", 
					"mail=", 
					"email=", 
					"bcc=", 
					"userlist=",
					"cachert=", 
					"cachesites=", 
					"cachenodes=", 
					"squeeze=", 
					"policysavedb=", 
					"status", 
					"help"]
		(opts, argv) = getopt.getopt(sys.argv[1:], "h", longopts)
	except getopt.GetoptError, err:
		print "Error: " + err.msg
		usage()
		sys.exit(1)

	for (opt, optval) in opts:
		if opt in ["--debug"]:
			config.debug = bool(int(optval))
			print "Running in DEBUG mode. Copying DB & "
			print "caching correspondences. NO SQUEEZING."
		elif opt in ["--mail"]:
			config.mail = bool(int(optval))
			print "NO EMAILS SENT."
		elif opt in ["--email"]:
			config.email = optval
		elif opt in ["--bcc"]:
			config.bcc = bool(int(optval))
		elif opt in ["--userlist"]:
			if len(optval) == 0:
				config.userlist = None
			else:
				config.userlist = optval
		elif opt in ["--cachert"]:
			config.cachert = bool(int(optval))
		elif opt in ["--cachesites"]:
			config.cachesites = bool(int(optval))
		elif opt in ["--cachenodes"]:
			config.cachenodes = bool(int(optval))
		elif opt in ["--policysavedb"]:
			config.policysavedb = bool(int(optval))
		elif opt in ["--squeeze"]:
			config.squeeze = bool(int(optval))
		elif opt in ["--status"]:
			#print summary(names)
			sys.exit(0)
		else:
			usage()
			sys.exit(0)

	config.save()
	usage()


if __name__ == '__main__':
	main()
