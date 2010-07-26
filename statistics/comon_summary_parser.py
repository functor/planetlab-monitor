#!/usr/bin/python

import sys, os, time, bz2

if len(sys.argv) != 2 :
	print 'usage: bz2comonlogfile'
	sys.exit()

filename = sys.argv[1]
start_time = time.time()
if not ('dump_comon_' in filename and filename.endswith('bz2')) :
	print 'not a comon log file:'
	sys.exit()

def str_to_ts(date_str, format="%Y-%m-%d"):
   ts = time.mktime(time.strptime(date_str, format))
   return ts


# .../dump_cotop_20080101 -> 2008-01-01
indx = filename.rfind('dump_comon_') + len('dump_comon') + 1
date = filename[indx:indx+8]
date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
ts = str_to_ts(date)

# read in bz2 log file
bzobj = bz2.BZ2File(filename, mode = 'r')
lines = bzobj.readlines()

last_time = 0
entry = {}
processed_tags = set()

# keep track of malformed entries
n_badTS = 0
n_ambigTS = 0
n_NA = {}

important_tags = ['Start:', 'Name:', 'RespTime:']

def get_field(table, *args):
	pos = table
	l = len(args)
	for i,v in enumerate(args[:-1]):
		if v not in pos:
			pos[v] = {}
		pos = pos[v]
	v = args[-1]
	if args[-1] not in pos:
		pos[v] = 0
	return pos[v]

def set_field(table, *args):
	pos = table
	l = len(args)
	#get_field(table, *args[0:-1])
	for i,v in enumerate(args[:-2]):
		pos = pos[v]
	pos[args[-2]] = args[-1]

def isValid(entry):
	# check important_tags
	for t in important_tags:
		if t not in entry: 
			#print "bad entry", entry
			return False

	try:
		if 'Uptime:' in entry:
			float(entry['Uptime:'])
	except:
		#print "uptime fault"
		return False

	return True

hs = {} # HOST SUMMARY 

# Process log
for line in lines :
	line = line.strip()
	if line == '' :
		#Process timestamp
		try :
			this_time = int(entry['Start:'][0])
			fmtime = time.strftime('%D %T', time.localtime(this_time))
			ambigTS = this_time < last_time
			if ambigTS :
				n_ambigTS += 1
			else :
				last_time = this_time
			#outcsv.write('%d,%s' % (this_time, ambigTS))
		except KeyError :
			continue
		except :
			n_badTS += 1
			entry = {}
			processed_tags = set()
			continue
		#Process other fields
		#try : 


		if True:

			if not isValid(entry):
				entry = {}
				processed_tags = set()
				continue

			h = entry['Name:']

			if h not in hs:
				get_field(hs,h,'offline') 
				get_field(hs,h,'online') 
				get_field(hs,h,'uptime') 

			try:
				if len(entry['RespTime:'].split()) > 1:
					set_field(hs,h,'offline', get_field(hs,h,'offline') + 1)
				else:
					set_field(hs,h,'online', get_field(hs,h,'online') + 1)
					set_field(hs,h,'uptime', max(get_field(hs,h,'uptime'),entry['Uptime:']) )
			except:
				#print "except resptime"
				continue


		#except KeyError :
		##	print "key error! on hostname: %s" % h
		#	continue

		entry = {}
		processed_tags = set()
	else :
		words = line.split()
		tag = words[0]
		if tag in processed_tags : 	# start over, since a tag is repeating
			entry = {}
			processed_tags = set()
		entry[tag] = " ".join(words[1:len(words)])
		processed_tags.add(tag)

# finished processing log file
			
# clean up memory objs
#outcsv.close()
bzobj.close()
lines = ''

online = 0
offline = 0
uptimes = []
#print "number of hosts:%s" % len(hs)
for h in hs:
	if hs[h]['uptime'] > 0: uptimes.append(float(hs[h]['uptime']))
	if hs[h]['online'] > hs[h]['offline']:
		online += 1
	else:
		offline += 1

l = len(uptimes)
uptimes.sort()
end_time = time.time()
print date, ts, online+offline, online, offline, uptimes[0], uptimes[l/4], uptimes[l/2], uptimes[l/2+l/4], uptimes[-1], end_time-start_time, filename
