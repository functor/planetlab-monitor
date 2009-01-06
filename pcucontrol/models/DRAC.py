from pcucontrol.reboot import *

class DRAC(PCUControl):
	supported_ports = [22,443,5869]
	def run_drac(self, node_port, dryrun):
		print "trying racadm_reboot..."
		return racadm_reboot(self.host, self.username, self.password, node_port, dryrun)

	def run_ssh(self, node_port, dryrun):
		ssh_options="-o StrictHostKeyChecking=no "+\
		            "-o PasswordAuthentication=yes "+\
					"-o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		if not s.login(self.host, self.username, self.password, ssh_options,
						original_prompts="Dell", login_timeout=Transport.TELNET_TIMEOUT):
			raise ExceptionPassword("Invalid Password")

		print "logging in..."
		s.send("\r\n\r\n")
		try:
			# Testing Reboot ?
			#index = s.expect(["DRAC 5", "[%s]#" % self.username ])
			# NOTE: be careful to escape any characters used by 're.compile'
			index = s.expect(["\$", "\[%s\]#" % self.username ])
			print "INDEX:", index
			if dryrun:
				if index == 0:
					s.send("racadm getsysinfo")
				elif index == 1:
					s.send("getsysinfo")
			else:
				if index == 0:
					s.send("racadm serveraction powercycle")
				elif index == 1:
					s.send("serveraction powercycle")
				
			s.send("exit")

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before expected Prompt")
		except pexpect.TIMEOUT:
			print s
			raise ExceptionPrompt("Timeout before expected Prompt")

		s.close()

		return 0

class DRACDefault(PCUControl):
	supported_ports = [22,443,5869]
	def run_ssh(self, node_port, dryrun):
		self.transport.open(self.host, self.username)
		self.transport.sendPassword(self.password)

		print "logging in..."
		self.transport.write("\r\n")
		# Testing Reboot ?
		if dryrun:
			self.transport.ifThenSend("[%s]#" % self.username, "getsysinfo")
		else:
			# Reset this machine
			self.transport.ifThenSend("[%s]#" % self.username, "serveraction powercycle")

		self.transport.ifThenSend("[%s]#" % self.username, "exit")

		self.transport.close()
		return 0

### rebooting Dell systems via RAC card
# Marc E. Fiuczynski - June 01 2005
# tested with David Lowenthal's itchy/scratchy nodes at UGA
#
def runcmd(command, args, username, password, timeout = None):

	result = [None]
	result_ready = threading.Condition()

	def set_result(x):

		result_ready.acquire()
		try:
			result[0] = x
		finally:
			result_ready.notify()
			result_ready.release()

	def do_command(command, username, password):

		try:
			# Popen4 is a popen-type class that combines stdout and stderr
			p = popen2.Popen4(command)

			# read all output data
			p.tochild.write("%s\n" % username)
			p.tochild.write("%s\n" % password)
			p.tochild.close()
			data = p.fromchild.read()

			while True:
				# might get interrupted by a signal in poll() or waitpid()
				try:
					retval = p.wait()
					set_result((retval, data))
					break
				except OSError, ex:
					if ex.errno == errno.EINTR:
						continue
					raise ex
		except Exception, ex:
			set_result(ex)

	if args:
		command = " ".join([command] + args)

	worker = threading.Thread(target = do_command, args = (command, username, password, ))
	worker.setDaemon(True)
	result_ready.acquire()
	worker.start()
	result_ready.wait(timeout)
	try:
		if result == [None]:
			raise Exception, "command timed-out: '%s'" % command
	finally:
		result_ready.release()
	result = result[0]

	if isinstance(result, Exception):
		raise result
	else:
		(retval, data) = result
		if os.WIFEXITED(retval) and os.WEXITSTATUS(retval) == 0:
			return data
		else:
			out = "system command ('%s') " % command
			if os.WIFEXITED(retval):
				out += "failed, rc = %d" % os.WEXITSTATUS(retval)
			else:
				out += "killed by signal %d" % os.WTERMSIG(retval)
			if data:
				out += "; output follows:\n" + data
			raise Exception, out

def racadm_reboot(host, username, password, port, dryrun):
	global verbose

	ip = socket.gethostbyname(host)
	try:
		cmd = "/usr/sbin/racadm"
		os.stat(cmd)
		if not dryrun:
			output = runcmd(cmd, ["-r %s -i serveraction powercycle" % ip],
				username, password)
		else:
			output = runcmd(cmd, ["-r %s -i getsysinfo" % ip],
				username, password)

		print "RUNCMD: %s" % output
		if verbose:
			logger.debug(output)
		return 0

	except Exception, err:
		logger.debug("runcmd raised exception %s" % err)
		if verbose:
			logger.debug(err)
		return err
