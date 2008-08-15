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
vals['princeton_comon'] = get_value('princeton_comon')
vals['princeton_comon_running'] = get_value('princeton_comon_running')
vals['princeton_comon_procs'] = get_value('princeton_comon_procs')


rows = ""
fb = database.dbLoad("findbad")
packed_values = []
for mynode in fb['nodes'].keys():
	fbnode = fb['nodes'][mynode]['values']
	row = []
	row.append(mynode)
	add=True
	for key in ['ssh', 'state', 'nm', 'princeton_comon', 'princeton_comon_running', 'princeton_comon_procs']:
		if key not in fbnode: 
			row.append('nokey')
		else:
			if vals[key] and vals[key] == fbnode[key]:
				add = True & add
			elif not vals[key]:
				add = True & add
			else:
				add = False

			row.append(fbnode[key])

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
for value in ['num', 'host', 'ssh', 'state', 'NM', 'comon<br>dir', 'comon<br>vserver', 'comon<br>procs']:
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
		
d = Document(t)
print d
