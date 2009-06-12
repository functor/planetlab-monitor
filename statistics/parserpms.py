#!/usr/bin/python

import sys
import os
import md5

def list_to_md5(strlist):
	digest = md5.new()
	for f in strlist:
		digest.update(f)

	return digest.hexdigest()

while True:
	line = sys.stdin.readline()
	if not line:
		break
	line = line.strip()
	fields = line.split()
	host = fields[1]
	rpms = fields[2:]
	rpms.sort()
	if len(rpms) != 0:
		sum = list_to_md5(rpms)
		print sum, host
