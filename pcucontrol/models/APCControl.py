from pcucontrol.reboot import *

class APCControl(PCUControl):
	supported_ports = [22,23,80,443]
	reboot_sequence = []

	def run(self, node_port, dryrun):
		print "RUNNING!!!!!!!!!!!!"
		if self.transport.type == Transport.HTTPS or self.type == Transport.HTTP:
			print "APC via http...."
			return self.run_http_or_https(node_port, dryrun)
		else:
			print "APC via telnet/ssh...."
			return self.run_telnet_or_ssh(node_port, dryrun)
	
	def run_ssh(self, node_port, dryrun):
		return self.run_telnet_or_ssh(node_port, dryrun)
	def run_telnet(self, node_port, dryrun):
		return self.run_telnet_or_ssh(node_port, dryrun)

	def run_telnet_or_ssh(self, node_port, dryrun):
		self.transport.open(self.host, self.username)
		self.transport.sendPassword(self.password)

		first = True
		for val in self.reboot_sequence:
			if first:
				self.transport.ifThenSend("\r\n> ", val, ExceptionPassword)
				first = False
			else:
				self.transport.ifThenSend("\r\n> ", val)

		if not dryrun:
			self.transport.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"YES\r\n",
							ExceptionSequence)
		else:
			self.transport.ifThenSend("Enter 'YES' to continue or <ENTER> to cancel", 
							"", ExceptionSequence)
		self.transport.ifThenSend("Press <ENTER> to continue...", "", ExceptionSequence)

		self.transport.close()
		return 0

	def run_http(self, node_port, dryrun):
		return self.run_http_or_https(node_port, dryrun)
	def run_https(self, node_port, dryrun):
		return self.run_http_or_https(node_port, dryrun)

	def run_http_or_https(self, node_port, dryrun):
		if not dryrun:
			# send reboot signal.
			# TODO: send a ManualPCU() reboot request for this PCU.
			# NOTE: this model defies automation because, the port numbering
			# 	and the form numbers are not consistent across models.  There is
			# 	not direct mapping from port# to form#.
			return "Manual Reboot Required"

		else:
			# TODO: also send message for https, since that doesn't work this way...
			if self.transport.type == Transport.HTTPS:
				cmd = self.get_https_cmd()
			elif self.transport.type == Transport.HTTP:
				cmd = self.get_http_cmd()
			else:
				raise ExceptionNoTransport("Unsupported transport for http command")

		cmd = cmd % ( self.username, self.password, self.host)
		print "CMD: %s" % cmd

		p = os.popen(cmd)
		result = p.read()
		if len(result.split('\n')) > 2:
			self.logout()
			return 0
		else:
			# NOTE: an error has occurred, so no need to log out.
			print "RESULT: ", result
			return result

	def get_https_cmd(self):
		version = self.get_version()
		print "VERSION: %s" % version
		if "AP96" in version:
			cmd = "curl -s --insecure --user '%s:%s' https://%s/outlets.htm " + \
				  " | grep -E '^[^<]+' " + \
				  " | grep -v 'Protected Object' "
		else:
			# NOTE: no other case known right now...
			cmd = "curl -s --insecure --user '%s:%s' https://%s/outlets.htm " + \
				  " | grep -E '^[^<]+' " + \
				  " | grep -v 'Protected Object' "
			
		return cmd
	
	def get_http_cmd(self):
		version = self.get_version()
		print "VERSION: %s" % version
		if "AP7900" in version:
			cmd = "curl -s --anyauth --user '%s:%s' http://%s/rPDUout.htm | grep -E '^[^<]+'" 
		elif "AP7920" in version:
			cmd = "curl -s --anyauth --user '%s:%s' http://%s/ms3out.htm | grep -E '^[^<]+' " 
		else:
			# default case...
			print "USING DEFAULT"
			cmd = "curl -s --anyauth --user '%s:%s' http://%s/ms3out.htm | grep -E '^[^<]+' " 
			
		return cmd

	def get_version(self):
		# NOTE: this command returns and formats all data.
		#cmd = """curl -s --anyauth --user '%s:%s' http://%s/about.htm """ +
		#      """ | sed -e "s/<[^>]*>//g" -e "s/&nbsp;//g" -e "/^$/d" """ +
		#	  """ | awk '{line=$0 ; if ( ! /:/ && length(pline) > 0 ) \
		#	  		     { print pline, line } else { pline=line} }' """ + 
		#	  """ | grep Model """

		# NOTE: we may need to return software version, no model version to
		# 		know which file to request on the server.

		if self.transport.type == Transport.HTTP:
			cmd = """curl -s --anyauth --user '%s:%s' http://%s/about.htm """ + \
				  """ | sed -e "s/<[^>]*>//g" -e "s/&nbsp;//g" -e "/^$/d" """ + \
				  """ | grep -E "AP[[:digit:]]+" """
				  #""" | grep -E "v[[:digit:]].*" """
		elif self.transport.type == Transport.HTTPS:
			cmd = """curl -s --insecure --user '%s:%s' https://%s/about.htm """ + \
				  """ | sed -e "s/<[^>]*>//g" -e "s/&nbsp;//g" -e "/^$/d" """ + \
				  """ | grep -E "AP[[:digit:]]+" """
				  #""" | grep -E "v[[:digit:]].*" """
		else:
			raise ExceptionNoTransport("Unsupported transport to get version")

		cmd = cmd % ( self.username, self.password, self.host)
		p = os.popen(cmd)
		result = p.read()
		return result.strip()

	def logout(self):
		# NOTE: log out again, to allow other uses to access the machine.
		if self.transport.type == Transport.HTTP:
			cmd = """curl -s --anyauth --user '%s:%s' http://%s/logout.htm """ + \
				  """ | grep -E '^[^<]+' """
		elif self.transport.type == Transport.HTTPS:
			cmd = """curl -s --insecure --user '%s:%s' http://%s/logout.htm """ + \
				  """ | grep -E '^[^<]+' """
		else:
			raise ExceptionNoTransport("Unsupported transport to logout")

		cmd = cmd % ( self.username, self.password, self.host)
		p = os.popen(cmd)
		print p.read()

class APCControl12p3(APCControl):
	def run_telnet_or_ssh(self, node_port, dryrun):
		self.reboot_sequence = ["1", "2", str(node_port), "3"]
		return super(APCControl12p3, self).run_telnet_or_ssh(node_port, dryrun)

class APCControl1p4(APCControl):
	def run_telnet_or_ssh(self, node_port, dryrun):
		self.reboot_sequence = ["1", str(node_port), "4"]
		return super(APCControl1p4, self).run_telnet_or_ssh(node_port, dryrun)

class APCControl121p3(APCControl):
	def run_telnet_or_ssh(self, node_port, dryrun):
		self.reboot_sequence = ["1", "2", "1", str(node_port), "3"]
		return super(APCControl121p3, self).run_telnet_or_ssh(node_port, dryrun)

class APCControl121p1(APCControl):
	def run_telnet_or_ssh(self, node_port, dryrun):
		self.reboot_sequence = ["1", "2", "1", str(node_port), "1", "3"]
		return super(APCControl121p1, self).run_telnet_or_ssh(node_port, dryrun)

class APCControl13p13(APCControl):
	def run_telnet_or_ssh(self, node_port, dryrun):
		self.reboot_sequence = ["1", "3", str(node_port), "1", "3"]
		return super(APCControl13p13, self).run_telnet_or_ssh(node_port, dryrun)
