from pcucontrol.reboot import *

class BayTechRPC3NC(PCUControl):
	supported_ports = [22,23]
	def run_telnet(self, node_port, dryrun):
		return self.run_ssh(node_port, dryrun)

	def run_ssh(self, node_port, dryrun):
		self.transport.open(self.host, self.username, None, "Enter user name:")
		self.transport.sendPassword(self.password, "Enter Password:")

		#self.transport.ifThenSend("RPC-16>", "Status")
		self.transport.ifThenSend("RPC3-NC>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.transport.ifThenSend("(Y/N)?", "N")
		else:
			self.transport.ifThenSend("(Y/N)?", "Y")
		self.transport.ifThenSend("RPC3-NC>", "")

		self.transport.close()
		return 0

class BayTechGeorgeTown(PCUControl):
	supported_ports = [22,23]
	def run_telnet(self, node_port, dryrun):
		return self.run_ssh(node_port, dryrun)
	def run_ssh(self, node_port, dryrun):
		# NOTE: The georgetown pcu always drops the first connection, 
		self.transport.open(self.host, self.username, None, "Enter")
		self.transport.close()
		time.sleep(1)
		self.transport.open(self.host, self.username, None, "Enter user name:")
		self.transport.sendPassword(self.password, "Enter Password:")

		self.transport.ifThenSend("RPC-16>", "Reboot %d" % node_port)

		# Reboot Outlet  N        (Y/N)?
		if dryrun:
			self.transport.ifThenSend("(Y/N)?", "N")
		else:
			self.transport.ifThenSend("(Y/N)?", "Y")
		self.transport.ifThenSend("RPC-16>", "")

		self.transport.close()
		return 0


class BayTechRPC16(PCUControl):
	supported_ports = [22,23]
	def run_telnet(self, node_port, dryrun):
		return self.run_ssh(node_port, dryrun)
	def run_ssh(self, node_port, dryrun):
		self.transport.open(self.host, self.username, None, "Enter user name:")
		self.transport.sendPassword(self.password, "Enter Password:")

		#self.transport.ifThenSend("RPC-16>", "Status")

		self.transport.ifThenSend("RPC-16>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.transport.ifThenSend("(Y/N)?", "N")
		else:
			self.transport.ifThenSend("(Y/N)?", "Y")
		self.transport.ifThenSend("RPC-16>", "")

		self.transport.close()
		return 0

class BayTechCtrlCUnibe(PCUControl):
	"""
		For some reason, these units let you log in fine, but they hang
		indefinitely, unless you send a Ctrl-C after the password.  No idea
		why.
	"""
	supported_ports = [22]
	def run_ssh(self, node_port, dryrun):
		print "BayTechCtrlC %s" % self.host

		ssh_options="-o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		if not s.login(self.host, self.username, self.password, ssh_options):
			raise ExceptionPassword("Invalid Password")
		# Otherwise, the login succeeded.

		# Send a ctrl-c to the remote process.
		print "sending ctrl-c"
		s.send(chr(3))

		# Control Outlets  (5 ,1).........5
		try:
			#index = s.expect("Enter Request")
			index = s.expect(["Enter Request :"])

			if index == 0:
				print "3"
				s.send("3\r\n")
				time.sleep(5)
				index = s.expect(["DS-RPC>", "Enter user name:"])
				if index == 1:
					s.send(self.username + "\r\n")
					time.sleep(5)
					index = s.expect(["DS-RPC>"])

				if index == 0:
					print "Reboot %d" % node_port
					time.sleep(5)
					s.send("Reboot %d\r\n" % node_port)

					time.sleep(5)
					index = s.expect(["\(Y/N\)\?", "Port in use", "DS-RPC>"])
					if index == 0:
						if dryrun:
							print "sending N"
							s.send("N\r\n")
						else:
							print "sending Y"
							s.send("Y\r\n")
					elif index == 1:
						raise ExceptionPrompt("PCU Reported 'Port in use.'")
					elif index == 2:
						raise ExceptionSequence("Issued command 'Reboot' failed.")

				time.sleep(5)
				index = s.expect(["DS-RPC>"])
				#print "got prompt back"

			s.close()

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before expected Prompt")
		except pexpect.TIMEOUT:
			raise ExceptionPrompt("Timeout before expected Prompt")

		return 0

class BayTechCtrlC(PCUControl):
	"""
		For some reason, these units let you log in fine, but they hang
		indefinitely, unless you send a Ctrl-C after the password.  No idea
		why.
	"""
	supported_ports = [22]
	def run_ssh(self, node_port, dryrun):
		print "BayTechCtrlC %s" % self.host

		ssh_options="-o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		try:
			if not s.login(self.host, self.username, self.password, ssh_options):
				raise ExceptionPassword("Invalid Password")
		except pexpect.EOF:
			raise ExceptionNoTransport("No Connection Possible")
			
			
		# Otherwise, the login succeeded.

		# Send a ctrl-c to the remote process.
		print "SENDING ctrl-c"
		s.send(chr(3))

		# Control Outlets  (5 ,1).........5
		try:
			print "EXPECTING: ", "Enter Request :"
			index = s.expect(["Enter Request :"])

			if index == 0:
				print "SENDING: 5"
				s.send("5\r\n")
				print "EXPECTING: ", "DS-RPC>"
				index = s.expect(["DS-RPC>", "Enter user name:", "Port in use."])
				if index == 1:
					print "sending username"
					s.send(self.username + "\r\n")
					index = s.expect(["DS-RPC>"])
				elif index == 2:
					raise ExceptionPrompt("PCU Reported 'Port in use.'")

				if index == 0:
					print "SENDING: Reboot %d" % node_port
					s.send("Reboot %d\r\n" % node_port)

					print "SLEEPING: 5"
					time.sleep(5)
					print "EXPECTING: ", "Y/N?"
					index = s.expect(["\(Y/N\)\?", "Port in use", "DS-RPC>"])
					if index == 0:
						if dryrun:
							print "sending N"
							s.send("N\r\n")
						else:
							print "SENDING: Y"
							s.send("Y\r\n")
					elif index == 1:
						raise ExceptionPrompt("PCU Reported 'Port in use.'")
					elif index == 2:
						raise ExceptionSequence("Issued command 'Reboot' failed.")

				# NOTE: for some reason, the script times out with the
				# following line.  In manual tests, it works correctly, but
				# with automated tests, evidently it fails.
				print "SLEEPING: 5"
				time.sleep(5)
				#print "TOTAL--", s.allstr, "--EOT"
				index = s.expect(["DS-RPC>"])
				print "got prompt back"

			s.close()

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before 'Enter Request' Prompt")
		except pexpect.TIMEOUT:
			raise ExceptionPrompt("Timeout before Prompt")

		return 0


class BayTech5CtrlC(PCUControl):
	"""
		For some reason, these units let you log in fine, but they hang
		indefinitely, unless you send a Ctrl-C after the password.  No idea
		why.
	"""
	supported_ports = [22]
	def run_ssh(self, node_port, dryrun):
		print "BayTech5CtrlC %s" % self.host

		ssh_options="-o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no"
		s = pxssh.pxssh()
		try:
			if not s.login(self.host, self.username, self.password, ssh_options):
				raise ExceptionPassword("Invalid Password")
		except pexpect.EOF:
			raise ExceptionNoTransport("No Connection Possible")
			
			
		# Otherwise, the login succeeded.
		# Control Outlets  (5 ,1).........5
		try:
			print "EXPECTING: ", "Enter Request :"
			s.send("\r\n")
			time.sleep(2)
			index = s.expect(["Enter Request"])

			if index == 0:
				print "SENDING: 5"
				s.send("5\r\n")
				print "EXPECTING: ", "DS-RPC>"
				time.sleep(3)
				# Send a ctrl-c to the remote process.
				#print "SENDING ctrl-c"
				#s.send(chr(3))

				index = s.expect(["DS-RPC>", "Enter user name:", "Port in use."])
				if index == 1:
					print "sending username"
					s.send(self.username + "\r\n")
					index = s.expect(["DS-RPC>"])
				elif index == 2:
					raise ExceptionPrompt("PCU Reported 'Port in use.'")

				if index == 0:
					print "SENDING: Reboot %d" % node_port
					#s.send("Reboot %d\r\n" % node_port)
					s.send("Reboot %d\r" % node_port)

					print "SLEEPING: 5"
					time.sleep(5)
					print "EXPECTING: ", "Y/N?"
					index = s.expect(["\(Y/N\)\?", "Port in use", "DS-RPC>"])
					if index == 0:
						if dryrun:
							print "sending N"
							s.send("N\r\n")
						else:
							print "SENDING: Y"
							s.send("Y\r\n")
					elif index == 1:
						raise ExceptionPrompt("PCU Reported 'Port in use.'")
					elif index == 2:
						raise ExceptionSequence("Issued command 'Reboot' failed.")

				# NOTE: for some reason, the script times out with the
				# following line.  In manual tests, it works correctly, but
				# with automated tests, evidently it fails.
				print "SLEEPING: 5"
				time.sleep(5)
				#print "TOTAL--", s.allstr, "--EOT"
				index = s.expect(["DS-RPC>"])
				print "got prompt back"

			s.close()

		except pexpect.EOF:
			raise ExceptionPrompt("EOF before 'Enter Request' Prompt")
		except pexpect.TIMEOUT:
			raise ExceptionPrompt("Timeout before Prompt")

		return 0

class BayTech(PCUControl):
	supported_ports = [22,23]

	def run_telnet(self, node_port, dryrun):
		return self.run_ssh(node_port, dryrun)

	def run_ssh(self, node_port, dryrun):
		self.transport.open(self.host, self.username)
		self.transport.sendPassword(self.password)

		# Control Outlets  (5 ,1).........5
		self.transport.ifThenSend("Enter Request :", "5")

		# Reboot N
		try:
			self.transport.ifThenSend("DS-RPC>", "Reboot %d" % node_port, ExceptionNotFound)
		except ExceptionNotFound, msg:
			# one machine is configured to ask for a username,
			# even after login...
			print "msg: %s" % msg
			self.transport.write(self.username + "\r\n")
			time.sleep(5)
			self.transport.ifThenSend("DS-RPC>", "Reboot %d" % node_port)

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.transport.ifThenSend("(Y/N)?", "N")
		else:
			self.transport.ifThenSend("(Y/N)?", "Y")
		time.sleep(5)
		self.transport.ifThenSend("DS-RPC>", "")

		self.transport.close()
		return 0
