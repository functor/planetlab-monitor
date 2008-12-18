#!/usr/bin/python

import threading
import socket
import os
import popen2
#import logger

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

def racadm_reboot(host, username, password, dryrun, state="powercycle"):

	ip = socket.gethostbyname(host)
	try:
		cmd = "/usr/sbin/racadm"
		os.stat(cmd)
		if not dryrun:
			output = runcmd(cmd, ["-r %s -i serveraction %s" % (ip, state)],
				username, password)
		else:
			output = runcmd(cmd, ["-r %s -i getsysinfo" % ip],
				username, password)

		print "RUNCMD: %s" % output
		return 0

	except Exception, err:
		#logger.debug("runcmd raised exception %s" % err)
		print "runcmd raised exception %s" % err
		return -1


from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(ip="", user="", password="", dryrun=False, state="powercycle")
parser.add_option("-d", "", dest="dryrun", action="store_true",
					help="enable dryrun tests.  no action is taken")
parser.add_option("-r", "", dest="ip", metavar="nodename.edu", 
					help="A single node name to add to the nodegroup")
parser.add_option("-u", "", dest="user", metavar="username",
					help="")
parser.add_option("-s", "", dest="state", metavar="powercycle",
					help="")
parser.add_option("-p", "", dest="password", metavar="password",
					help="")
(options, args) = parser.parse_args()

if __name__ == '__main__':
	print options
	if	options.ip is not "" and \
		options.user is not "" and \
		options.password is not "":

		racadm_reboot(options.ip, options.user, options.password, options.dryrun, options.state)
	else:
		parser.print_help()
