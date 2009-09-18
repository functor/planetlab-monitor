from pcucontrol.reboot import *

class IPAL(PCUControl):
	""" 
		This now uses a proprietary format for communicating with the PCU.  I
		prefer it to Telnet, and Web access, since it's much lighter weight
		and, more importantly, IT WORKS!! HHAHHHAHAHAHAHAHA!
	"""
	supported_ports = [9100,23,80]

	def format_msg(self, data, cmd):
		esc = chr(int('1b',16))
		return "%c%s%c%s%c" % (esc, self.password, esc, data, cmd) # esc, 'q', chr(4))
	
	def recv_noblock(self, s, count):
		import errno

		try:
			# TODO: make sleep backoff, before stopping.
			time.sleep(8)
			ret = s.recv(count, socket.MSG_DONTWAIT)
		except socket.error, e:
			if e[0] == errno.EAGAIN:
				#raise Exception(e[1])
				raise ExceptionNotFound(e[1])
			elif e[0] == errno.ETIMEDOUT:
				raise ExceptionTimeout(e[1])
			else:
				# TODO: not other exceptions.
				raise Exception(e)
		return ret

	#def run(self, node_port, dryrun):
	#	if self.type == Transport.IPAL:
	#		ret = self.run_ipal(node_port, dryrun)
	#		if ret != 0:
	#			ret2 = self.run_telnet(node_port, dryrun)
	#			if ret2 != 0:
	#				return ret
	#			return ret2
	#		return ret
	#	elif self.type == Transport.TELNET:
	#		return self.run_telnet(node_port, dryrun)
	#	else:
	#		raise ExceptionNoTransport("Unimplemented Transport for IPAL")
	
	def run_telnet(self, node_port, dryrun):
		# TELNET version of protocol...
		self.transport.open(self.host)
		## XXX Some iPals require you to hit Enter a few times first
		self.transport.ifThenSend("Password >", "\r\n\r\n", ExceptionNotFound)
		self.transport.ifThenSend("Password >", "\r\n\r\n", ExceptionNotFound)
		# Login
		self.transport.ifThenSend("Password >", self.password, ExceptionPassword)
		self.transport.write("\r\n\r\n")
		if not dryrun: # P# - Pulse relay
			print "node_port %s" % node_port
			self.transport.ifThenSend("Enter >", 
							"P%s"%node_port, 
							ExceptionNotFound)
			print "send newlines"
			self.transport.write("\r\n\r\n")
			print "after new lines"
		# Get the next prompt
		print "wait for enter"
		self.transport.ifElse("Enter >", ExceptionTimeout)
		print "closing "
		self.transport.close()
		return 0

	def run_ipal(self, node_port, dryrun):
		import errno

		power_on = False

		print "open socket"
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			print "connect"
			s.connect((self.host, 9100))
		except socket.error, e:
			s.close()
			if e[0] == errno.ECONNREFUSED:
				# cannot connect to remote host
				raise ExceptionNotFound(e[1])
			elif e[0] == errno.ETIMEDOUT:
				raise ExceptionTimeout(e[1])
			else:
				# TODO: what other conditions are there?
				raise Exception(e)
				
		# get current status
		print "Checking status"
		s.send(self.format_msg("", 'O'))
		ret = self.recv_noblock(s, 8)
		print "Current status is '%s'" % ret

		if ret == '':
			raise Exception("Status returned 'another session already open' on %s %s : %s" % (self.host, node_port, ret))
				
		if node_port < len(ret):
			status = ret[node_port]
			if status == '1':
				# up
				power_on = True
			elif status == '0':
				# down
				power_on = False
			elif status == '6':
				raise ExceptionPort("IPAL reported 'Cable Error' on %s socket %s : %s" % (self.host, node_port, ret))
			else:
				raise Exception("Unknown status for PCU %s socket %s : %s" % (self.host, node_port, ret))
		else:
			raise Exception("Mismatch between configured port and PCU %s status: %s %s" % (self.host, node_port, ret))
			

		if not dryrun:
			if power_on:
				print "Pulsing %s" % node_port
				s.send(self.format_msg("%s" % node_port, 'P'))
			else:
				# NOTE: turn power on ; do not pulse the port.
				print "Power was off, so turning on ..."
				s.send(self.format_msg("%s" % node_port, 'E'))
				#s.send(self.format_msg("%s" % node_port, 'P'))

			print "Receiving response."
			ret = self.recv_noblock(s, 8)
			print "Current status is '%s'" % ret

			if node_port < len(ret):
				status = ret[node_port]
				if status == '1':
					# up
					power_on = True
				elif status == '0':
					# down
					power_on = False
				elif status == '6':
					raise ExceptionPort("IPAL reported 'Cable Error' on %s socket %s : %s" % (self.host, node_port, ret))
				else:
					raise Exception("Unknown status for PCU %s socket %s : %s" % (self.host, node_port, ret))
			else:
				raise Exception("Mismatch between configured port and PCU %s status: %s %s" % (self.host, node_port, ret))

			if power_on:
				return 0
			else:
				return "Failed Power On"

		s.close()
		return 0
