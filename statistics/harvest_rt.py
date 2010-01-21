#!/usr/bin/python

import os
import time
from datetime import datetime, timedelta
import sys
from monitor.common import Time

def popen(cmdstr):
	f = os.popen(cmdstr)
	ret = f.read()
	return ret

def datetime_fromstr(str):
	if '-' in str:
		try:
			tup = time.strptime(str, "%Y-%m-%d")
		except:
			tup = time.strptime(str, "%Y-%m-%d-%H:%M")
	elif '/' in str:
		tup = time.strptime(str, "%m/%d/%Y")
	else:
		tup = time.strptime(str, "%m/%d/%Y")
	ret = datetime.fromtimestamp(time.mktime(tup))
	return ret


def main():
	queue = sys.argv[1]
	d1 = datetime_fromstr(sys.argv[2])
	iterations = int(sys.argv[3])
	i = 0
	while i < iterations:
		d1_s = d1.strftime("%Y-%m-%d")
		d2 = d1 + timedelta(1)
		d2_s = d2.strftime("%Y-%m-%d")
		query = "Queue='%s' and " % queue 
		query = query + "Told > '%s' and Told < '%s'" % (d1_s, d2_s)
		cmd = """rt ls -t ticket "%s" | grep -v "No matching" | wc -l  """ % query
		#print cmd
		ret = popen(cmd)
		print "%s,%s,%s" % (d1_s, Time.dt_to_ts(d1), ret[:-1])
		d1=d2
		i += 1

if __name__ == "__main__":
	main()
