#!/usr/bin/python

from monitor import config

for attr in dir(config):
	val = config.__getattribute__(attr)
	if (attr[0].isupper() and attr[1].isupper()) or ('email' in attr):
		print '%s="%s" ' % (attr, val)
