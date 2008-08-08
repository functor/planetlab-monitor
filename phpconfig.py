#!/usr/bin/python

import monitorconfig

print "<?php"
for attr in dir(monitorconfig):
	val = monitorconfig.__getattribute__(attr)
	if attr[0].isupper():
		print "define('%s', '%s'); " % (attr, val)
print "?>"
