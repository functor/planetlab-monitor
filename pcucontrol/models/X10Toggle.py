
from pcucontrol.reboot import *
### rebooting x10toggle based systems addressed by port
# Marc E. Fiuczynski - May 31 2005
# tested on 4-ports models known as PSE505-FR
# uses ssh and password to login to an account
# that will cause the system to be powercycled.

TELNET_TIMEOUT = 120
def telnet_answer(telnet, expected, buffer):
	global verbose

	output = telnet.read_until(expected, TELNET_TIMEOUT)
	#if verbose:
	#	logger.debug(output)
	if output.find(expected) == -1:
		raise ExceptionNotFound, "'%s' not found" % expected
	else:
		telnet.write(buffer + "\r\n")

def x10toggle_reboot(ip, username, password, port, dryrun):
	global verbose

	ssh = None
	try:
		ssh = pyssh.Ssh(username, ip)
		ssh.open()

		# Login
		telnet_answer(ssh, "password:", password)

		if not dryrun:
			# Reboot
			telnet_answer(ssh, "x10toggle>", "A%d" % port)

		# Close
		output = ssh.close()
		if verbose:
			logger.debug(output)
		return 0

	except Exception, err:
		if verbose:
			logger.debug(err)
		if ssh:
			output = ssh.close()
			if verbose:
				logger.debug(output)
		return errno.ETIMEDOUT
