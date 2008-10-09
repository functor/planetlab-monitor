#!/usr/bin/python

import cgi
import cgitb; 
from monitor import database
import time
cgitb.enable()

from HyperText.HTML import A, BR, IMG, TABLE, TR, TH, TD, EM, quote_body
from HyperText.Documents import Document
print "Content-Type: text/html\r\n"

form = cgi.FieldStorage()

def get(fb, path):
    indexes = path.split("/")
    values = fb
    for index in indexes:
        if index in values:
            values = values[index]
        else:
            return None
    return values

def diff_time(timestamp, abstime=True):
	import math
	now = time.time()
	if timestamp == None:
		return "unknown"
	if abstime:
		diff = now - timestamp
	else:
		diff = timestamp
	# return the number of seconds as a difference from current time.
	t_str = ""
	if diff < 60: # sec in min.
		t = diff / 1
		t_str = "%s sec ago" % int(math.ceil(t))
	elif diff < 60*60: # sec in hour
		t = diff / (60)
		t_str = "%s min ago" % int(math.ceil(t))
	elif diff < 60*60*24: # sec in day
		t = diff / (60*60)
		t_str = "%s hrs ago" % int(math.ceil(t))
	elif diff < 60*60*24*14: # sec in week
		t = diff / (60*60*24)
		t_str = "%s days ago" % int(math.ceil(t))
	elif diff <= 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*7)
		t_str = "%s wks ago" % int(math.ceil(t))
	elif diff > 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*30)
		t_str = "%s mnths ago" % int(t)
	return t_str

def get_value(val):
	
	if form.has_key(val):
		retvalue = form.getvalue(val)
	else:
		retvalue = None
	
	return retvalue

vals = {}
vals['ssh'] = get_value('ssh')
vals['state'] = get_value('state')
vals['nm'] = get_value('nm')
vals['dns'] = None
vals['readonlyfs'] = None
vals['plcnode/last_contact'] = None
vals['comonstats/uptime'] = None
vals['princeton_comon'] = get_value('princeton_comon')
vals['princeton_comon_running'] = get_value('princeton_comon_running')
vals['princeton_comon_procs'] = get_value('princeton_comon_procs')


rows = ""
fb = database.dbLoad("findbad")
packed_values = []
node_count = 0
for mynode in fb['nodes'].keys():
	fbnode = fb['nodes'][mynode]['values']
	row = []
	row.append(mynode)
	add=True
	if 'readonlyfs' in fbnode:
		if 'Read-only file system' in fbnode['readonlyfs']:
			fbnode['readonlyfs'] = 'Y'
		else:
			fbnode['readonlyfs'] = '_'

	if 'dns' in fbnode:
		if 'boot.planet-lab.org has address' in fbnode['dns']:
			fbnode['dns'] = '_'
		else:
			fbnode['dns'] = 'N'
			
	for key in ['ssh', 'state', 'plcnode/last_contact', 'readonlyfs', 'dns', 'nm', 'princeton_comon', 'princeton_comon_running', 'princeton_comon_procs', 'comonstats/uptime']:
		if get(fbnode, key) is None:
			row.append('nokey')
		else:
			if vals[key] is not None and vals[key] in get(fbnode, key):
				add = True & add
			elif vals[key] is None:
				add = True & add
			else:
				add = False
			
			if 'last_contact' in key:
				t = time.time()
				lc = get(fbnode,key)
				diff = ((t - lc) // (60*60*6)) * 6
				row.append(-int(diff))
			else:
				row.append(get(fbnode,key))
	if add:
		packed_values.append(row)



def rowcmp(x,y):
	for i in range(1,len(x)):
		if x[i] == y[i]: continue
		if x[i] < y[i]: return -1
		if x[i] > y[i]: return 1
	return 0

packed_values.sort(rowcmp)

t = TABLE(border=1)
r = TR()
for value in ['num', 'host', 'ssh', 'state', 'last<br>contact', 'readonlyfs', 'dns', 'NM', 'comon<br>dir', 'comon<br>vserver', 'comon<br>procs']:
	r.append(TD(value))
t.append(r)

i=1
for row in packed_values:
	r = TR()
	r.append(TD(i))
	for value in row:
		r.append(TD(value))
	i+=1 
	t.append(r)
		
#r = TR()
#r.append(TD(node_count))
#t.append(r)

d = Document(t)
print d
