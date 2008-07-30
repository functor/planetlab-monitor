import csv
from glob import glob
import os
import time

def time_to_str(t):
	return time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(t))

def get_filelist_from_dir(dirname):
	filelist = glob("%s/*.out" % dirname)

	ret_list = []
	for file in filelist:
		ret_list.append(file)
	return ret_list

def get_hostlist_from_dir(dirname):
	filelist = glob("%s/*.out" % dirname)

	ret_list = []
	for file in filelist:
		ret_list.append([os.path.basename(file)[:-4], ''])
	return ret_list

def csv_to_hash(r):
	ret = {}
	for line in r:
		(k,v) = (line[0], line[1])
		if k not in ret:
			ret[k] = v
		else:
			# multiple values for the same key
			if isinstance(ret[k], list):
				ret[k].append(v)
			else:
				ret[k] = [ret[k], v]
	return ret

def getcsv(file):
	return csv_to_hash(csv.reader(open(file,'r')))
