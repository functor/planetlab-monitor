#!/usr/bin/python
import pickle
import os
import getopt
import sys
import __main__
from optparse import OptionParser

config_command = False

XMLRPC_SERVER="https://boot.planet-lab.org/PLCAPI/"
def parse_bool(option, opt_str, value, parser):
	if opt_str in ["--debug"]:
		parser.values.debug = int(int(value))
	elif opt_str in ["--mail"]:
		parser.values.mail = int(int(value))
	elif opt_str in ["--bcc"]:
		parser.values.bcc = int(int(value))
	elif opt_str in ["--policysavedb"]:
		parser.values.policysavedb = int(int(value))
	elif opt_str in ["--squeeze"]:
		parser.values.squeeze = int(int(value))
	else:
		print "blue"

def getListFromFile(file):
	f = open(file, 'r')
	list = []
	for line in f:
		line = line.strip()
		list += [line]
	return list

class config:
	debug=0
	mail=0
	bcc=0
	email="soltesz@cs.utk.edu"
	run=False
	checkopt=False
	squeeze=0
	policysavedb=0
	__file = ".config"

	def __init__(self, parser=None):
		if os.path.exists(self.__file): # file exists, read that.
			f = open(self.__file, 'r')
			o = pickle.load(f)
			self.__dict__.update(o)
			f.close()

		if parser == None:
			self.parser = OptionParser()
		else:
			self.parser = parser

		self.parser.set_defaults(debug = self.debug,
								mail = self.mail,
								bcc  = self.bcc,
								email = self.email,
								run = self.run,
								checkopt = False,
								squeeze = self.squeeze,
								policysavedb = self.policysavedb)

		self.parser.add_option("", "--debug", dest="debug",
						  help="Enable debugging", 
						  type="int",
						  metavar="[0|1]",
						  action="callback", 
						  callback=parse_bool)
		self.parser.add_option("", "--mail", dest="mail",
						  help="Enable sending email",
						  type="int",
						  metavar="[0|1]",
						  action="callback", 
						  callback=parse_bool)
		self.parser.add_option("", "--bcc", dest="bcc",
						  help="Include BCC to user",
						  type="int",
						  metavar="[0|1]",
						  action="callback", 
						  callback=parse_bool)
		self.parser.add_option("", "--squeeze", dest="squeeze",
						  help="Squeeze sites or not",
						  type="int",
						  metavar="[0|1]",
						  action="callback", 
						  callback=parse_bool)
		self.parser.add_option("", "--policysavedb", dest="policysavedb",
						  help="Save the policy event database after a run",
						  type="int",
						  metavar="[0|1]",
						  action="callback", 
						  callback=parse_bool)
		self.parser.add_option("", "--checkopt", dest="checkopt", 
						  action="store_true",
						  help="print current options")
		self.parser.add_option("", "--run", dest="run", 
						  action="store_true",
						  help="Perform monitor or print configs")
		self.parser.add_option("", "--email", dest="email",
						  help="Specify an email address to use for mail when "+\
								 "debug is enabled or for bcc when it is not")
		
		# config_command is needed to keep subsequent loads of config() from
		# trying to parse the arguments that have already been parsed by
		# the new main().
		if parser == None and config_command:
			print "calling parse_args"
			self.parse_args()

	def parse_args(self):
		#print "self: %s" % self
		#import traceback
		#print traceback.print_stack()
		#print "Ccalling parse_args"
		(options, args) = self.parser.parse_args()
		#for o in options.__dict__:
		#	print "optin: %s == %s" % (o, options.__dict__[o])
		self.__dict__.update(options.__dict__)
		self.__dict__['args'] = args
		self.save(options)
		if options.checkopt:
			self.usage()
		#	print "\nAdd --run to actually perform the command"
			sys.exit(1)

	def getListFromFile(self, file):
		f = open(file, 'r')
		list = []
		for line in f:
			line = line.strip()
			list += [line]
		return list

	def print_values(self):
		exclude = ['parser']
		for key in self.__dict__.keys():
			if key not in exclude:
				print "%20s == %s" % (key, self.__dict__[key])
		
	def save(self, options=None):
		f = open(self.__file, 'w')
		if options == None:
			o = {'debug': self.debug, 
				 'mail': self.mail, 
				 'bcc': self.bcc, 
				 'email':self.email,
				 'squeeze':self.squeeze,
				 'policysavedb':self.policysavedb}
		else:
			o = options.__dict__

		pickle.dump(o, f)
		f.close()

	def usage(self):
		self.print_values()
		self.parser.print_help()


def main():
	""" Start threads, do some housekeeping, then daemonize. """
	# Defaults
	global config_command
	config_command = True
	config = __main__.config()

	try:
		print "acalling parse_args"
		config.parse_args()
		
	except Exception, err:
		print "Error: %s " %  err
		config.usage()
		sys.exit(1)

	config.usage()


if __name__ == '__main__':
	main()
