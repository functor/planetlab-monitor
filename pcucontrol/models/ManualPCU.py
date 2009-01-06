from pcucontrol.reboot import *

class ManualPCU(PCUControl):
	supported_ports = [22,23,80,443]

	def run_http(self, node_port, dryrun):
		if not dryrun:
			# TODO: send email message to monitor admin requesting manual
			# intervention.  This should always be an option for ridiculous,
			# custom jobs.
			pass
		return 0

