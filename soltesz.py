import os
import sys
import pickle
noserial=False
try:
	from PHPSerialize import *
	from PHPUnserialize import *
except:
	print >>sys.stderr, "PHPSerial db type not allowed."
	noserial=True

import inspect
import shutil
from config import config
config = config()

DEBUG= 0
PICKLE_PATH="pdb"

def dbLoad(name, type=None):
	return SPickle().load(name, type)

def dbExists(name, type=None):
	#if self.config.debug:
	#	name = "debug.%s" % name
	return SPickle().exists(name, type)

def dbDump(name, obj=None, type=None):
	# depth of the dump is 2 now, since we're redirecting to '.dump'
	return SPickle().dump(name, obj, type, 2)

def if_cached_else_refresh(cond, refresh, name, function, type=None):
	s = SPickle()
	if refresh:
		if not config.debug and s.exists("production.%s" % name, type):
			s.remove("production.%s" % name, type)
		if config.debug and s.exists("debug.%s" % name, type):
			s.remove("debug.%s" % name, type)

	return if_cached_else(cond, name, function, type)

def if_cached_else(cond, name, function, type=None):
	s = SPickle()
	if (cond and s.exists("production.%s" % name, type)) or \
	   (cond and config.debug and s.exists("debug.%s" % name, type)):
		o = s.load(name, type)
	else:
		o = function()
		if cond:
			s.dump(name, o, type)	# cache the object using 'name'
			o = s.load(name, type)
		# TODO: what if 'o' hasn't been converted...
	return o

class SPickle:
	def __init__(self):
		pass

	def if_cached_else(self, cond, name, function, type=None):
		if cond and self.exists("production.%s" % name, type):
			o = self.load(name, type)
		else:
			o = function()
			if cond:
				self.dump(name, o, type)	# cache the object using 'name'
		return o

	def __file(self, name, type=None):
		if type == None:
			return "%s/%s.pkl" % (PICKLE_PATH, name)
		else:
			if noserial:
				raise Exception("No PHPSerializer module available")

			return "%s/%s.phpserial" % (PICKLE_PATH, name)
		
	def exists(self, name, type=None):
		return os.path.exists(self.__file(name, type))

	def remove(self, name, type=None):
		return os.remove(self.__file(name, type))

	def load(self, name, type=None):
		""" 
		In debug mode, we should fail if neither file exists.
			if the debug file exists, reset name
			elif the original file exists, make a copy, reset name
			else neither exist, raise an error
		Otherwise, it's normal mode, if the file doesn't exist, raise error
		Load the file
		"""

		if config.debug:
			if self.exists("debug.%s" % name, type):
				name = "debug.%s" % name
			elif self.exists("production.%s" % name, type):
				debugname = "debug.%s" % name
				if not self.exists(debugname, type):
					name = "production.%s" % name
					shutil.copyfile(self.__file(name, type), self.__file(debugname, type))
				name = debugname
			else:	# neither exist
				raise Exception, "No such pickle based on %s" % self.__file("debug.%s" % name, type)
		else:
			if not self.exists("production.%s" % name, type):
				raise Exception, "No such file %s" % name
			name = "production.%s" % name

		print "loading %s" % self.__file(name, type)
		f = open(self.__file(name, type), 'r')
		if type == None:
			o = pickle.load(f)
		else:
			if noserial:
				raise Exception("No PHPSerializer module available")
			s = PHPUnserialize()
			o = s.unserialize(f.read())
		f.close()
		return o
			
	
	# use the environment to extract the data associated with the local
	# variable 'name'
	def dump(self, name, obj=None, type=None, depth=1):
		if obj == None:
			o = inspect.getouterframes(inspect.currentframe())
			up1 = o[depth][0] # get the frame one prior to (up from) this frame
			argvals = inspect.getargvalues(up1)
			# TODO: check that 'name' is a local variable; otherwise this would fail.
			obj = argvals[3][name] # extract the local variable name 'name'
		if not os.path.isdir("%s/" % PICKLE_PATH):
			os.mkdir("%s" % PICKLE_PATH)
		if config.debug:
			name = "debug.%s" % name
		else:
			name = "production.%s" % name
		f = open(self.__file(name, type), 'w')
		if type == None:
			pickle.dump(obj, f)
		else:
			if noserial:
				raise Exception("No PHPSerializer module available")
			s = PHPSerialize()
			f.write(s.serialize(obj))
		f.close()
		return


COMMAND_TIMEOUT = 60
ssh_options = { 'StrictHostKeyChecking':'no', 
				'BatchMode':'yes', 
				'PasswordAuthentication':'no',
				'ConnectTimeout':'%s' % COMMAND_TIMEOUT}
from select import select 
class CMD:
	def __init__(self):
		pass

	def run_noexcept(self, cmd):

		(f_in, f_out, f_err) = os.popen3(cmd)
		lout, lin, lerr = select([f_out,f_err], [], [], COMMAND_TIMEOUT*2)
		if len(lin) == 0 and len(lout) == 0 and len(lerr) == 0:
			# Reached a timeout!
			print "TODO: kill subprocess: '%s'" % cmd
			# TODO: kill subprocess??
			return ("", "SCRIPTTIMEOUT")
		o_value = f_out.read()
		e_value = ""
		if o_value == "":	# An error has occured
			e_value = f_err.read()

		o_value = o_value.strip()
		e_value = e_value.strip()

		f_out.close()
		f_in.close()
		f_err.close()
		return (o_value, e_value)

	def run(self, cmd):

		(f_in, f_out, f_err) = os.popen3(cmd)
		value = f_out.read()
		if value == "":
			raise Exception, f_err.read()
		value = value.strip()

		f_out.close()
		f_in.close()
		f_err.close()
		return value

		

class SSH(CMD):
	def __init__(self, user, host, options = ssh_options):
		self.options = options
		self.user = user
		self.host = host
		return

	def __options_to_str(self):
		options = ""
		for o,v in self.options.iteritems():
			options = options + "-o %s=%s " % (o,v)
		return options

	def run(self, cmd):
		cmd = "ssh %s %s@%s '%s'" % (self.__options_to_str(), 
									self.user, self.host, cmd)
		return CMD.run(self, cmd)

	def get_file(self, rmt_filename, local_filename=None):
		if local_filename == None:
			local_filename = "./"
		cmd = "scp -B %s %s@%s:%s %s" % (self.__options_to_str(), 
									self.user, self.host, 
									rmt_filename, local_filename)
		# output :
		# 	errors will be on stderr,
		#   success will have a blank stderr...
		return CMD.run_noexcept(self, cmd)

	def run_noexcept(self, cmd):
		cmd = "ssh %s %s@%s '%s'" % (self.__options_to_str(), 
									self.user, self.host, cmd)
		return CMD.run_noexcept(self, cmd)

	def runE(self, cmd):
		cmd = "ssh %s %s@%s '%s'" % (self.__options_to_str(), 
									self.user, self.host, cmd)
		if ( DEBUG == 1 ):
			print cmd,
		(f_in, f_out, f_err) = os.popen3(cmd)

		value = f_out.read()
		if value == "":	# An error has occured
			value = f_err.read()
			value = value.strip()

		if ( DEBUG == 1 ):
			print " == %s" % value
		f_out.close()
		f_in.close()
		f_err.close()
		return value.strip()
		
import time
class MyTimer:
	def __init__(self):
		self.start = time.time()

	def end(self):
		self.end = time.time()
		t = self.end-self.start
		return t

	def diff(self):
		self.end = time.time()
		t = self.end-self.start
		self.start = self.end
		return t
