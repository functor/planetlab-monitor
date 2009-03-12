from pcucontrol.reboot import *
from distutils.sysconfig import get_python_lib; 

class HPiLO(PCUControl):
	supported_ports = [22,443]
	def run(self, node_port, dryrun):
		if self.type == Transport.SSH:
			return self.run_ssh(node_port, dryrun)
		elif self.type == Transport.HTTP or self.type == Transport.HTTPS:
			return self.run_https(node_port, dryrun)
		else:
			raise ExceptionNoTransport("Unimplemented Transport for HPiLO %s" % self.type)

	def run_ssh(self, node_port, dryrun):

		self.transport.open(self.host, self.username)
		self.transport.sendPassword(self.password)

		# </>hpiLO-> 
		self.transport.ifThenSend("</>hpiLO->", "cd system1")

		# Reboot Outlet  N	  (Y/N)?
		if dryrun:
			self.transport.ifThenSend("</system1>hpiLO->", "POWER")
		else:
			# Reset this machine
			self.transport.ifThenSend("</system1>hpiLO->", "reset")

		self.transport.ifThenSend("</system1>hpiLO->", "exit")

		self.transport.close()
		return 0
		
	def run_https(self, node_port, dryrun):

		locfg = command.CMD()

		cmd_str = get_python_lib(1) + "/pcucontrol/models/hpilo/"
		
		cmd = cmd_str + "locfg.pl -s %s -f %s -u %s -p '%s' | grep 'MESSAGE' | grep -v 'No error'" % (
					self.host, cmd_str+"iloxml/Get_Network.xml", 
					self.username, self.password)
		sout, serr = locfg.run_noexcept(cmd)

		if sout.strip() != "" or serr.strip() != "":
			print "sout: %s" % sout.strip()
			return sout.strip() + serr.strip()

		if not dryrun:
			locfg = command.CMD()
			cmd = cmd_str + "locfg.pl -s %s -f %s -u %s -p '%s' | grep 'MESSAGE' | grep -v 'No error'" % (
						self.host, cmd_str+"iloxml/Reset_Server.xml", 
						self.username, self.password)
			sout, serr = locfg.run_noexcept(cmd)

			if sout.strip() != "":
				print "sout: %s" % sout.strip()
				#return sout.strip()

		return 0
