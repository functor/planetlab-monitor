#!/usr/bin/python

#from monitor.reboot import *
import sys
import time

def main():
	#try:
	#	if "test" in sys.argv:
	#		dryrun = True
	#	else:
	#		dryrun = False
#
#		for node in sys.argv[1:]:
#			if node == "test": continue
#
#			print "Rebooting %s" % node
#			if reboot_policy(node, True, dryrun):
#				print "success"
#			else:
#				print "failed"
#	except Exception, err:
#		import traceback; traceback.print_exc()
#		from monitor.common import email_exception
#		email_exception(node)
#		print err
    return 

if __name__ == '__main__':
	#main()
	f = open("/tmp/reboot", 'a')
	f.write("reboot %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()
