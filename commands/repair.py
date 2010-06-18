#!/usr/bin/python

import time
import sys
import os

if __name__ == '__main__':
	f = open("/tmp/repair", 'a')
	f.write("repair %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()
