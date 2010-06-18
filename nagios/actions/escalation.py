#!/usr/bin/python

import time
import sys


if __name__ == '__main__':
	f = open("/tmp/escalation", 'a')
	f.write("escalation %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()
