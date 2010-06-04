#!/usr/bin/python

from monitor.reboot import *
import time

def main():
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter('LOGGER - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	try:
		if "test" in sys.argv:
			dryrun = True
		else:
			dryrun = False

		for node in sys.argv[1:]:
			if node == "test": continue

			print "Rebooting %s" % node
			if reboot_policy(node, True, dryrun):
				print "success"
			else:
				print "failed"
	except Exception, err:
		import traceback; traceback.print_exc()
		from monitor.common import email_exception
		email_exception(node)
		print err

if __name__ == '__main__':
	main()
	f = open("/tmp/rebootlog", 'a')
	f.write("reboot %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()
