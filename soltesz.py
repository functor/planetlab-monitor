import os
import sys
import pickle
noserial=False
try:
	from PHPSerialize import *
	from PHPUnserialize import *
except:
	#print >>sys.stderr, "PHPSerial db type not allowed."
	noserial=True

import inspect
import shutil
import config

import config

DEBUG= 0
PICKLE_PATH=config.MONITOR_DATA_ROOT

class ExceptionTimeout(Exception): pass

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
			if   self.exists("production.%s" % name, type):
				name = "production.%s" % name
			elif self.exists(name, type):
				name = name
			else:
				raise Exception, "No such file %s" % name
				

		#print "loading %s" % self.__file(name, type)
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


COMMAND_TIMEOUT = 60
ssh_options = { 'StrictHostKeyChecking':'no', 
				'BatchMode':'yes', 
				'PasswordAuthentication':'no',
				'ConnectTimeout':'%s' % COMMAND_TIMEOUT}
from select import select 
import subprocess
import signal

class Sopen(subprocess.Popen):
	def kill(self, signal = signal.SIGTERM):
		os.kill(self.pid, signal)

def read_t(stream, count, timeout=COMMAND_TIMEOUT*2):
	lin, lout, lerr = select([stream], [], [], timeout)
	if len(lin) == 0:
		raise ExceptionTimeout("TIMEOUT Running: %s" % cmd)

	return stream.read(count)

class CMD:
	def __init__(self):
		pass

	def run_noexcept(self, cmd, timeout=COMMAND_TIMEOUT*2):

		#print "CMD.run_noexcept(%s)" % cmd
		try:
			return CMD.run(self,cmd,timeout)
		except ExceptionTimeout:
			import traceback; print traceback.print_exc()
			return ("", "SCRIPTTIMEOUT")
			
	def system(self, cmd, timeout=COMMAND_TIMEOUT*2):
		(o,e) = self.run(cmd, timeout)
		self.output = o
		self.error = e
		if self.s.returncode is None:
			self.s.wait()
		return self.s.returncode

	def run(self, cmd, timeout=COMMAND_TIMEOUT*2):

		#print "CMD.run(%s)" % cmd
		s = Sopen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		self.s = s
		(f_in, f_out, f_err) = (s.stdin, s.stdout, s.stderr)
		#print "calling select(%s)" % timeout
		lout, lin, lerr = select([f_out], [], [f_err], timeout)
		#print "TIMEOUT!!!!!!!!!!!!!!!!!!!"
		if len(lin) == 0 and len(lout) == 0 and len(lerr) == 0:
			# Reached a timeout!  Nuke process so it does not hang.
			#print "KILLING"
			s.kill(signal.SIGKILL)
			raise ExceptionTimeout("TIMEOUT Running: %s" % cmd)
		else:
			#print "RETURNING"
			#print len(lin), len(lout), len(lerr)
			pass

		o_value = ""
		e_value = ""

		#print "reading from f_out"
		if len(lout) > 0: o_value = f_out.read()
		#print "reading from f_err"
		if len(lerr) > 0: e_value = f_err.read()

		#print "striping output"
		o_value = o_value.strip()
		e_value = e_value.strip()

		#print "OUTPUT", o_value, e_value

		#print "closing files"
		f_out.close()
		f_in.close()
		f_err.close()
		try:
			#print "s.kill()"
			s.kill()
			#print "after s.kill()"
		except OSError:
			# no such process, due to it already exiting...
			pass

		#print o_value, e_value
		return (o_value, e_value)

	def runargs(self, args, timeout=COMMAND_TIMEOUT*2):

		#print "CMD.run(%s)" % " ".join(args)
		s = Sopen(args, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		self.s = s
		(f_in, f_out, f_err) = (s.stdin, s.stdout, s.stderr)
		lout, lin, lerr = select([f_out], [], [f_err], timeout)
		if len(lin) == 0 and len(lout) == 0 and len(lerr) == 0:
			# Reached a timeout!  Nuke process so it does not hang.
			s.kill(signal.SIGKILL)
			raise ExceptionTimeout("TIMEOUT Running: %s" % cmd)
		o_value = f_out.read()
		e_value = ""
		if o_value == "":	# An error has occured
			e_value = f_err.read()

		o_value = o_value.strip()
		e_value = e_value.strip()

		f_out.close()
		f_in.close()
		f_err.close()
		try:
			s.kill()
		except OSError:
			# no such process, due to it already exiting...
			pass

		return (o_value, e_value)


class SSH(CMD):
	def __init__(self, user, host, port=22, options = ssh_options):
		self.options = options
		self.user = user
		self.host = host
		self.port = port
		return

	def __options_to_str(self):
		options = ""
		for o,v in self.options.iteritems():
			options = options + "-o %s=%s " % (o,v)
		return options

	def run(self, cmd, timeout=COMMAND_TIMEOUT*2):
		cmd = "ssh -p %s %s %s@%s '%s'" % (self.port, self.__options_to_str(), 
									self.user, self.host, cmd)
		#print "SSH.run(%s)" % cmd
		return CMD.run(self, cmd, timeout)

	def get_file(self, rmt_filename, local_filename=None):
		if local_filename == None:
			local_filename = "./"
		cmd = "scp -P %s -B %s %s@%s:%s %s" % (self.port, self.__options_to_str(), 
									self.user, self.host, 
									rmt_filename, local_filename)
		# output :
		# 	errors will be on stderr,
		#   success will have a blank stderr...
		return CMD.run_noexcept(self, cmd)

	def run_noexcept(self, cmd):
		cmd = "ssh -p %s %s %s@%s '%s'" % (self.port, self.__options_to_str(), 
									self.user, self.host, cmd)
		#print "SSH.run_noexcept(%s)" % cmd
		return CMD.run_noexcept(self, cmd)

	def run_noexcept2(self, cmd, timeout=COMMAND_TIMEOUT*2):
		cmd = "ssh -p %s %s %s@%s %s" % (self.port, self.__options_to_str(), 
									self.user, self.host, cmd)
		#print "SSH.run_noexcept2(%s)" % cmd
		r = CMD.run_noexcept(self, cmd, timeout)

		# XXX: this may be resulting in deadlocks... not sure.
		#if self.s.returncode is None:
		#	#self.s.kill()
		#	self.s.kill(signal.SIGKILL)
		#	self.s.wait()
		#	self.ret = self.s.returncode
		self.ret = -1

		return r

	def system2(self, cmd, timeout=COMMAND_TIMEOUT*2):
		cmd = "ssh -p %s %s %s@%s %s" % (self.port, self.__options_to_str(), 
									self.user, self.host, cmd)
		#print "SSH.system2(%s)" % cmd
		return CMD.system(self, cmd, timeout)

	def runE(self, cmd):
		cmd = "ssh -p %s %s %s@%s '%s'" % (self.port, self.__options_to_str(), 
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
