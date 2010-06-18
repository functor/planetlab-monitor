#!/usr/bin/python

import time
import sys
import os

from monitor.wrapper import plc

def argv_to_dict(argv):
	"""
		NOTE: very bare-bones, no error checking, will fail easily.
	"""
	d = {}
	prev=None
	for a in argv:
		if "--" == a[0:2]:
			prev = a[2:]
		elif "-" == a[0:1]:
			prev = a[1:]
		else:
			d[prev] = a
	return d

def main():
	d = argv_to_dict(sys.argv[1:])

	api = plc.api
	if 'hostname' in d or 'H' in d:
		try:
			hostname = d['host']
		except:
			hostname = d['H']
	else:
		print "UNKNOWN: argument error"
		sys.exit(3)

	try:
		n = api.GetNodes(hostname)[0]
	except:
		print "UNKNOWN: API failure"
		sys.exit(3)

	if n['last_contact']:
		t1 = n['last_contact']
	else:
		t1 = 0
	t2 = time.time()
	#print n['boot_state'], n['run_level'], t1, t2, t2-t1

	if t2-t1 < 60*60*30:
		if n['boot_state'] == n['run_level']:
			print "OK: bootstate matches runlevel and lastcontact is up to date"
			sys.exit(0)
		else:
			print "WARNING: bootstate does not match runlevel"
			sys.exit(1)
	else:
		print "CRITICAL: node last_contact is stale, assumed offline"
		sys.exit(2)


if __name__ == '__main__':
	f = open("/tmp/checkmode", 'a')
	f.write("checkmode %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
	f.close()
	main()
