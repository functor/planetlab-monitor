
from monitor import database
from datetime import datetime, timedelta
import os
import glob
import time

from monitor import config

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

def get_filefromglob(d, str, path="archive-pdb", returnlist=False):
	# TODO: This is aweful.
	startpath = os.getcwd()
	os.chdir(config.MONITOR_SCRIPT_ROOT + "/" + path)

	#archive = database.SPickle(path)
	glob_str = "%s*.%s.pkl" % (d.strftime("%Y-%m-%d"), str)
	fg_list = [ x[:-4] for x in glob.glob(glob_str) ]

	os.chdir(startpath)

	if returnlist:
		return sorted(fg_list)
	else:
		return fg_list[0]

def get_archive(path):
	full_path = config.MONITOR_SCRIPT_ROOT + "/" + path
	return database.SPickle(full_path)
	
def print_graph(data, begin, end, xaxis, offset=500, window=100):
	s1=[]
	s2=[]
	s3=[]
	for row in data:
		s1.append(row[0])
		s2.append(row[1])
		s3.append(row[2])
	
	delta=offset
	s1 = map(lambda x: x-delta, s1)
	rlow= zip(s1,s3)
	rhigh = zip(s1,s2)
	diff_low  = map(lambda x: x[0]-x[1], rlow)
	diff_high = map(lambda x: x[0]+x[1], rhigh)
	s1 = map(lambda x: str(x), s1)
	diff_low = map(lambda x: str(x), diff_low)
	diff_high = map(lambda x: str(x), diff_high)
	print s1
	print diff_low
	print diff_high
	print "http://chart.apis.google.com/chart?cht=lc&chds=0,100&chxt=x,y&chxl=0:%s1:|500|550|600&chs=700x200&chm=F,aaaaaa,1,-1,2&chd=t1:%s" % (xaxis, ",".join(s1) + "|" + ",".join(diff_low) + "|" + ",".join(s1) + "|" + ",".join(s1) +"|" + ",".join(diff_high) )

def get_xaxis(list, width=16, wide=False):
	# 3 for odd
	# 4 for even
	# 5 for wide odd
	# 6 for wide even
	list_len = len(list)
	if list_len == 0: return "||"

	is_even = list_len % 2 == 0
	#if is_even:
	#	xaxis = "|" + list[0][:width] + "|" + list[-1][:width] + "|"
	#else:
	xaxis = "|" + list[0][:width] + "|" + list[list_len/2 + 1][:width] + "|" + list[-1][:width] + "|"
	return xaxis

