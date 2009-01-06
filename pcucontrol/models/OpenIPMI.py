
from pcucontrol.reboot import *

class OpenIPMI(PCUControl):

	supported_ports = [80,443,623]

	# TODO: get exit codes to determine success or failure...
	def run_https(self, node_port, dryrun):

		if not dryrun:
			cmd = "ipmitool -I lanplus -H %s -U %s -P '%s' power cycle  "
			(i,p) = os.popen4(cmd % ( self.host, self.username, self.password) )
			result = p.read()
			print "RESULT: ", result
		else:
			cmd = "ipmitool -I lanplus -H %s -U %s -P '%s' user list  "
			(i,p) = os.popen4(cmd % ( self.host, self.username, self.password) )
			result = p.read()
			print "RESULT: ", result

		if "Error" in result:
			return result
		else:
			return 0
