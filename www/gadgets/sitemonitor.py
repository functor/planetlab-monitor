#!/usr/bin/python

import cgi
import cgitb
cgitb.enable()
print "Content-Type: text/html\r\n"

import time
from unified_model import *
from monitor import database
from HyperText.HTML import A, BR, IMG, TABLE, TR, TH, TD, EM, quote_body, CENTER
from HyperText.Documents import Document

form = cgi.FieldStorage()

print """
<style>
table {
	align: center;
    border-color: #ccc;
    border-width: 0 0 1px 1px;
    border-style: solid;
}
th {
    border-color: #fff;
    border-width: 1px 1px 1px 1px;
    border-style: solid;
    margin: 0;
    padding: 0px;
}
td {
    border-color: #ccc;
    border-width: 1px 1px 0 0;
    border-style: solid;
    margin: 0;
    padding: 3px;
}
</style>
"""

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
		t_str = "%s weeks ago" % int(math.ceil(t))
	elif diff > 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*30)
		t_str = "%s months ago" % int(t)
	return t_str

def get_value(val):
	
	if form.has_key(val):
		retvalue = form.getvalue(val)
	else:
		retvalue = None
	
	return retvalue

def state_to_color(state):
	if state == "BOOT":
		return "darkseagreen"
	elif state == "DEBUG":
		return "gold"
	elif state == "DOWN":
		return "indianred"
	else:
		return "lightgrey"

def main():
	
	if form.has_key('loginbase'):
		loginbase = form.getvalue('loginbase')
	else:
		loginbase = "undefined"

	fb = database.dbLoad("findbad")
	lb2hn = database.dbLoad("plcdb_lb2hn")
	pf = database.dbLoad("node_persistflags")

	# SETUP header
	t = TABLE(border="0", cellspacing="0", cellpadding="0")
	r = TR()

	if loginbase not in lb2hn:
		value = ("Select 'Edit settings' to enter your Site's loginbase.", "")
		r = TR(TD(value[0]))
		t.append(r)
	else:
		for value in ['Hostname', 'Since']:
			r.append(TH(value))
		t.append(r)
		nodes = lb2hn[loginbase]
		hostnames = [ n['hostname'] for n in nodes ]
		hostnames.sort()

		for host in hostnames:
			r = TR()
			color = state_to_color(fb['nodes'][host]['values']['state'])
			url = 'http://www.planet-lab.org/db/nodes/index.php?nodepattern=%s' % host
			td = TD(A(host, target='_blank', href=url), bgcolor=color)
			r.append(td)
			lc = pf[host].last_changed
			td = TD(diff_time(lc))
			r.append(td)
			t.append(r)
			
	#d = Document(t)
	print CENTER(t)

if __name__ == "__main__":
	main()
