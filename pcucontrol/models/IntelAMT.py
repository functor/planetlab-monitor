from pcucontrol.reboot import *
from distutils.sysconfig import get_python_lib; 

class IntelAMT(PCUControl):
	supported_ports = [16992]

	def run_amt(self, node_port, dryrun):

		cmd = command.CMD()
		# TODO: need to make this path universal; not relative to pwd.
		cmd_str = get_python_lib(1) + "/pcucontrol/models/intelamt/remoteControl"

		if dryrun:
			# NOTE: -p checks the power state of the host.
			# TODO: parse the output to find out if it's ok or not.
			cmd_str += " -p http://%s:16992/RemoteControlService  -user admin -pass '%s' " % (self.host, self.password )
		else:
			cmd_str += " -A http://%s:16992/RemoteControlService -user admin -pass '%s' " % (self.host, self.password )
			
		print cmd_str
		return cmd.system(cmd_str, Transport.TELNET_TIMEOUT)
