#!/usr/bin/python

import time
import sys
import os


def argv_to_dict(argv):
	"""
		NOTE: very bare-bones, no error checking, will fail easily.
	"""
	d = {}
	prev=None
	for a in argv:
		if "--" in a:
			prev = a[2:]
		else:
			d[prev] = a
	return d

if __name__ == '__main__':
	f = open("/tmp/myopsmail", 'a')
	f.write("mail %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()

	d = argv_to_dict(sys.argv[1:])
	command_line="""/usr/bin/printf "%%b" "***** MyOpsNagios %(hostnotificationnumber)s *****\\n\\nNotification Type: %(notificationtype)s\\nHost: %(hostname)s\\nState: %(hoststate)s\\nAddress: %(hostaddress)s\\nInfo: %(hostoutput)s\\n\\nDate/Time: %(longdatetime)s\\n" | /bin/mail -S replyto=monitor@planet-lab.org -s "** %(notificationtype)s Host Alert: %(hostname)s is %(hoststate)s **" %(contactemail)s""" % d
	os.system(command_line)


