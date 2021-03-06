import os
import sys
import pickle
import inspect
import shutil
import time
from monitor import config

noserial=False
try:
	from util.PHPSerialize import *
	from util.PHPUnserialize import *
except:
	#print >>sys.stderr, "PHPSerial db type not allowed."
	noserial=True

DEBUG= 0
PICKLE_PATH=config.MONITOR_DATA_ROOT

def lastModified(name, type=None):
	# TODO: fix for 'debug' mode also.
	t = SPickle().mtime("production.%s" % name, type)
	return t

def escapeName(name):
	"""
		automatically escape names passed to the db to make sensible-filenames without
		exposing this to users.
	"""
	return name.replace("/", "_")

def cachedRecently(name, length=int(config.cachetime), type=None):
	"""
		return true or false based on whether the modified time of the cached
		file is within 'length' minutes.
	"""
	name = name.replace("/", "_")
	if hasattr(config, 'cachecalls') and not config.cachecalls:
		# don't use cached calls if cachecalls is false
		return False

	try:
		t = lastModified(name, type)
	except:
		# file doesn't exist or we can't access it.
		return False

	current_time = time.time()
	if current_time > t + length*60:
		return False
	else:
		return True

def dbLoad(name, type=None):
	name = escapeName(name)
	return SPickle().load(name, type)

def dbExists(name, type=None):
	name = escapeName(name)
	return SPickle().exists(name, type)

def dbDump(name, obj=None, type=None):
	name = escapeName(name)
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
	def __init__(self, path=PICKLE_PATH):
		self.path = path

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
			return "%s/%s.pkl" % (self.path, name)
		else:
			if noserial:
				raise Exception("No PHPSerializer module available")

			return "%s/%s.phpserial" % (self.path, name)

	def mtime(self, name, type=None):
		f = os.stat(self.__file(name, type))
		return f[-2]
		
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
		#print "loading %s" % name

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
			if   self.exists("production.%s" % name, type):
				name = "production.%s" % name
			elif self.exists(name, type):
				name = name
			else:
				raise Exception, "No such file %s" % name
				

		#import traceback
		#print traceback.print_stack()
		#print "loading %s" % self.__file(name, type)
		#sys.stderr.write("-----------------------------\n")
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
		if not os.path.isdir("%s/" % self.path):
			os.mkdir("%s" % self.path)
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
