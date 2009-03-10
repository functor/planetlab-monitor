import os
from select import select 
import subprocess
import signal
import time
import traceback

DEBUG= 0

class ExceptionTimeout(Exception): pass
COMMAND_TIMEOUT = 60
ssh_options = { 'StrictHostKeyChecking':'no', 
				'BatchMode':'yes', 
				'PasswordAuthentication':'no',
				'ConnectTimeout':'%s' % COMMAND_TIMEOUT}

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
			print traceback.print_exc()
			return ("", "SCRIPTTIMEOUT")
		except:
			from monitor.common import email_exception
			email_exception()
			
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

		o_value = f_out.read()
		e_value = f_err.read()

		#print "striping output"
		o_value = o_value.strip()
		e_value = e_value.strip()

		#print "OUTPUT -%s-%s-" % (o_value, e_value)

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
