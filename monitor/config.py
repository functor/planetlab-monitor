#!/usr/bin/python

# load defaults from /etc/monitor.conf
# home/.monitor.conf
# $PWD/.monitor.conf
import os
import ConfigParser

class Options(object):
	def __init__(self):
		cp = ConfigParser.ConfigParser()
		cp.optionxform = str
		# load defaults from global, home dir, then $PWD
		cp.read(['/etc/monitor.conf', os.path.expanduser('~/.monitor.conf'), 
					   '.monitor.conf', 'monitor.conf'])
		self.cp = cp
		self.section = "default"
	def __getattr__(self, name):
		if name in self.cp.sections():
			self.section = name
			return self
		else:
			return self.cp.get(self.section, name)


import config
imported = False

def updatemodule(module, cf):
	module.__dict__.update(cf.__dict__)

def update_section(options, section, bool=False):
	# Place all default commandline values at the top level of this module
	for key in options.cp.options(section):
		if bool:
			config.__dict__.update({key : options.cp.getboolean(section, key)})
		else:
			config.__dict__.update({key : options.cp.get(section, key)})

def update(parseoptions):
	update_commandline()
	# now update the top-level module with all other args passed in here.
	for key in parseoptions.__dict__.keys():
		config.__dict__.update({key: parseoptions.__dict__[key]})

if not config.imported:
	imported = True

	#from config import options as config
	options = Options()
	update_section(options, 'commandline', True)
	update_section(options, 'monitorconfig')

#for i in dir(config):
#	if "__" not  in i:
#		print i, "==", config.__dict__[i]
#print "======================================"

