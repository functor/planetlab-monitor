from pcucontrol.reboot import *

class WTIIPS4(PCUControl):
	supported_ports = [23]
	def run_telnet(self, node_port, dryrun):
		self.transport.open(self.host)
		self.transport.sendPassword(self.password, "Enter Password:")

		self.transport.ifThenSend("IPS> ", "/Boot %s" % node_port)
		if not dryrun:
			self.transport.ifThenSend("Sure? (Y/N): ", "N")
		else:
			self.transport.ifThenSend("Sure? (Y/N): ", "Y")

		self.transport.ifThenSend("IPS> ", "")

		self.transport.close()
		return 0
