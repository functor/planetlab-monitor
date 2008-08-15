#!/usr/bin/python

import config

print "<?php"
for attr in dir(config):
	val = config.__getattribute__(attr)
	if attr[0].isupper() and attr[1].isupper():
		print "define('%s', '%s'); " % (attr, val)
print "?>"
