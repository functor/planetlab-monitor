#!/usr/bin/python
import soltesz
from config import config
from optparse import OptionParser
import string
from HyperText.HTML import A, BR, IMG, TABLE, TR, TH, TD, EM, quote_body
from HyperText.Documents import Document

import sys

categories = {}
ssherror = False
fb = {}

def sec2days(sec):
	if sec == "null":
		sec = -(60*60*24)
	sec = int(sec)
	return sec/(60*60*24)

def array_to_priority_map(array):
	""" Create a mapping where each entry of array is given a priority equal
	to its position in the array.  This is useful for subsequent use in the
	cmpMap() function."""
	map = {}
	count = 0
	for i in array:
		map[i] = count
		count += 1
	return map

def cmpValMap(v1, v2, map):
	if v1 in map and v2 in map and map[v1] < map[v2]:
		return 1
	elif v1 in map and v2 in map and map[v1] > map[v2]:
		return -1
	elif v1 in map and v2 in map:
		return 0
	else:
		raise Exception("No index %s or %s in map" % (v1, v2))

def cmpMap(l1, l2, index, map):
	if index in l1 and index in l2:
		if map[l1[index]] < map[l2[index]]:
			return -1
		elif map[l1[index]] > map[l2[index]]:
			return 1
		else:
			return 0
	else:
		return 0

def cmpLoginBase(l1, l2):
	#print "'" + l1['loginbase'] + "'"  + " < " + "'" + l2['loginbase'] + "'" + "<BR>"
	if l1['loginbase'] == l2['loginbase']:
		return 0
	elif l1['loginbase'] < l2['loginbase']:
		return -1
	elif l1['loginbase'] > l2['loginbase']:
		return 1
	else:
		return 0

def cmpState(l1, l2):
	map = array_to_priority_map([ 'BOOT', 'DEBUG', 'DOWN' ])
	return cmpMap(l1,l2,'state', map)

def cmpCategoryVal(v1, v2):
	map = array_to_priority_map([ None, 'ALPHA', 'PROD', 'OLDBOOTCD', 'UNKNOWN', 'FORCED', 'ERROR', ])
	return cmpValMap(v1,v2,map)

def cmpCategory(l1, l2):
	map = array_to_priority_map([ 'ALPHA', 'PROD', 'OLDBOOTCD', 'UNKNOWN', 'ERROR', ])
	return cmpMap(l1,l2,'category', map)

def cmpPCU(l1, l2):
	""" Either PCU or NOPCU"""
	map = array_to_priority_map([ 'PCU', 'NOPCU', 'UNKNOWN'])
	return cmpMap(l1, l2, 'pcu', map)

def cmpSSH(l1, l2):
	""" Either SSH or NOSSH """
	map = array_to_priority_map([ 'SSH', 'NOSSH'])
	return cmpMap(l1, l2, 'ssh', map)

def cmpDNS(l1,l2):
	""" Compare DNS states """
	map = array_to_priority_map([ 'OK', 'NOHOSTNAME', 'NOENTRY', 'MISMATCH'])
	return cmpMap(l1, l2, 'dnsmatch', map)
	
def cmpPing(l1,l2):
	""" Either PING or NOPING """
	map = array_to_priority_map([ 'PING', 'NOPING'])
	return cmpMap(l1, l2, 'ping', map)

def cmpUname(l1, l2):
	# Extract the kernel version from kernel -a string
	l_k1 = l1['kernel'].split()
	if len(l_k1) > 2:
		k1 = l_k1[2]
	else:
		return 1

	l_k2 = l2['kernel'].split()
	if len(l_k2) > 2:
		k2 = l_k2[2]
	else:
		return -1

	return cmp(k1, k2)

def cmpDays(l1, l2):
	if l1['comonstats'][config.comon] == "null":
		l1['comonstats'][config.comon] = -1
	if l2['comonstats'][config.comon] == "null":
		l2['comonstats'][config.comon] = -1
		
	if int(l1['comonstats'][config.comon]) > int(l2['comonstats'][config.comon]):
		return -1
	elif int(l1['comonstats'][config.comon]) < int(l2['comonstats'][config.comon]):
		return 1
	else:
		return 0

def ssh_error_to_str(str):
	ssh_error = ""
	if "Connection timed out" in str:
		ssh_error = "Timeout" 
	elif "Connection closed by remote host" in str:
		ssh_error = "Closed by remote host"
	elif "Connection refused" in str:
		ssh_error = "Connection refused"
	elif "Temporary failure in name resolution" in str:
		ssh_error = "Could not resolve name"
	elif "Name or service not known" in str:
		ssh_error = "Name not known"
	elif "Too many authentication failures" in str:
		ssh_error = "Disconnect: root auth failure"
	elif "Network is unreachable" in str:
		ssh_error = "Network is unreachable"
	elif "Connection reset by peer" in str:
		ssh_error = "Connection reset by peer"
	elif "WARNING" in str:
		ssh_error = "WARNING ssh key updated"
	else:
		ssh_error = str

	return ssh_error

def pcu_state(pcu_id):
	global fb

	if 'nodes' in fb and "id_%s" % pcu_id in fb['nodes'] \
		and 'values' in fb['nodes']["id_%s" % pcu_id]:
		rec = fb['nodes']["id_%s" % pcu_id]['values']
		if 'reboot' in rec:
			rb = rec['reboot']
			if rb == 0 or rb == "0":
				return 0
			elif "NetDown" == rb  or "Not_Run" == rb:
				return 1
			else:
				return -1
		else:
			return -1
	else:
		return -1 

def fields_to_html(fields, vals):
	global categories
	global ssherror
	pcu_colorMap = { -1 : 'indianred',
					  0 : 'darkseagreen',
					  1 : 'gold', }

	colorMap = { 'PING'  : 'darkseagreen',
				 'NOPING': 'darksalmon',
				 'SSH': 'darkseagreen',
				 'NOSSH': 'indianred',
				 'PCU': 'darkseagreen',
				 'NOPCU': 'lightgrey',
				 'OLDBOOTCD': 'crimson',
				 'DOWN': 'indianred',
				 'ALPHA': 'gold',
				 'ERROR': 'crimson',
				 'PROD': 'darkseagreen',
				 'DEBUG': 'darksalmon',
				 'DEBUG': 'darksalmon',
				 'BOOT': 'lightgreen'}
	r_str = ""
	f_prev = ""
	f_2prev = ""
	#print 'inside--------------'
	for f in fields:
		f = f.strip()
		#print f

		if f in ['DOWN', 'BOOT', 'DEBUG']:
			#key = "%s-%s-%s" % (f,f_prev,f_2prev)
			key = "%s-%s" % (f,f_prev)
			if key not in categories:
				categories[key] = 1
			else:
				categories[key] += 1

		#print "<pre>%s</pre><br>" % f
				
		if f in colorMap:
			bgcolor="bgcolor='%s'" % colorMap[f]
		else:
			bgcolor=""

		if f == 'NOSSH':
			if ssherror:
				if 'ssherror' in vals:
					str_ssh_error = ssh_error_to_str(vals['ssherror'])
				else:
					str_ssh_error = "NO SSHERROR in VALS"
				if str_ssh_error != "Timeout":
					r_str += """<td nowrap %s>%s<br><b><font size="-2">%s</font></b></td>""" % \
								(bgcolor,f,str_ssh_error)
				else:
					r_str += "<td %s>%s</td>" % (bgcolor, f)
			else:
				r_str += "<td %s>%s</td>" % (bgcolor, f)
		elif f == 'PCU':
			if len(vals['plcnode']['pcu_ids']) > 0:
				#print "pcu_id: %s<br>" % vals['plcnode']['pcu_ids'][0]
				#print "state: %s<br>" % pcu_state(vals['plcnode']['pcu_ids'][0])
				#print "color: %s<br>" % pcu_colorMap[pcu_state(vals['plcnode']['pcu_ids'][0])]
				bgcolor = "bgcolor='%s'" % pcu_colorMap[pcu_state(vals['plcnode']['pcu_ids'][0])]
				url = "<a href='/cgi-bin/printbadpcus.php#id%s'>PCU</a>" % vals['plcnode']['pcu_ids'][0]
				r_str += "<td nowrap %s>%s</td>" % (bgcolor, url)
		else:
			r_str += "<td nowrap %s>%s</td>" % (bgcolor, f)
		f_2prev = f_prev
		f_prev  = f
	
	return r_str



def main(sitefilter, catfilter, statefilter, comonfilter, nodeonlyfilter):
	global fb

	db = soltesz.dbLoad(config.dbname)
	fb = soltesz.dbLoad("findbadpcus")

	## Field widths used for printing
	maxFieldLengths = { 'nodename' : -45,
						'ping' : 6, 
						'ssh' : 6, 
						'pcu' : 7, 
						'category' : 9, 
						'state' : 5, 
						'kernel' : 10.65, 
						'comonstats' : 5, 
						'plcsite' : 12,
						'bootcd' : 10.65}
	## create format string based on config.fields
	fields = {}
	format = ""
	format_fields = []
	for f in config.fields.split(','):
		fields[f] = "%%(%s)s" % f
		#if f in maxFieldLengths:
		#	fields[f] = "%%(%s)%ds" % (f, maxFieldLengths[f])
		#else:
		#	fields[f] = "%%(%s)%ds" % (f, 10)

		format_fields.append(fields[f])
	#print fields
	for f in config.fields.split(','):
		format += fields[f] + " "
	#print format

	d_n = db['nodes']
	l_nodes = d_n.keys()

	# category by site
	#bysite = {}
	#for nodename in l_nodes:
	#	if 'plcsite' in d_n[nodename]['values'] and \
	#	'login_base' in d_n[nodename]['values']['plcsite']:
	#		loginbase = d_n[nodename]['values']['plcsite']['login_base']
	#		if loginbase not in bysite:
	#			bysite[loginbase] = []
	#		d_n[nodename]['values']['nodename'] = nodename
	#		bysite[loginbase].append(d_n[nodename]['values'])

	# d2 was an array of [{node}, {}, ...]
	# the bysite is a loginbase dict of [{node}, {node}]
	d2 = []
	import re
	if sitefilter != None:
		sf = re.compile(sitefilter)
	else:
		sf = None
	for nodename in l_nodes: 
		vals=d_n[nodename]['values'] 
		v = {}
		v.update(vals)
		v['nodename'] = nodename 
		if  'plcsite' in vals and  \
			'status' in vals['plcsite'] and  \
			vals['plcsite']['status'] == "SUCCESS":

			url = "<a href='printbadnodes.py?site=%s'>%s</a>" % ( vals['plcsite']['login_base'],
															 vals['plcsite']['login_base'])

			site_string = "%s %2s nodes :: %2s of %4s slices" % ( \
														url,
														vals['plcsite']['num_nodes'], 
														vals['plcsite']['num_slices'], 
														vals['plcsite']['max_slices'])
			loginbase = d_n[nodename]['values']['plcsite']['login_base']
		else:
			#print "ERROR: ", nodename, vals, "<br>"
			site_string = "<b>UNKNOWN</b>"
			loginbase = ""

		v['site_string'] = site_string
		v['loginbase'] = loginbase
		if (sitefilter != None and sf.match(loginbase) != None) or sitefilter == None:
			d2.append(v)
			

	if sitefilter != None:
		config.cmpcategory = True
	else:
		config.cmploginbase = True
		

	if config.cmploginbase:
		d2.sort(cmp=cmpLoginBase)
	elif config.cmpping:
		d2.sort(cmp=cmpPing)
	elif config.cmpdns:
		d2.sort(cmp=cmpDNS)
	elif config.cmpssh:
		d2.sort(cmp=cmpSSH)
	elif config.cmpcategory:
		d2.sort(cmp=cmpCategory)
	elif config.cmpstate:
		d2.sort(cmp=cmpState)
	elif config.cmpdays:
		d2.sort(cmp=cmpDays)
	elif config.cmpkernel:
		d2.sort(cmp=cmpUname)
	else:
		d2.sort(cmp=cmpCategory)
	

	if catfilter != None:	cf = re.compile(catfilter)
	else: 					cf = None

	if statefilter != None:	stf = re.compile(statefilter)
	else: 					stf = None

	if comonfilter != None:	cmf = re.compile(comonfilter)
	else: 					cmf = None

	#l_loginbase = bysite.keys()
	#l_loginbase.sort()
	if nodeonlyfilter == None:
		print "<table width=80% border=1>"

	prev_sitestring = ""
	for row in d2:

		vals = row

		if (catfilter != None and cf.match(vals['category']) == None):
			continue

		if (statefilter != None and stf.match(vals['state']) == None):
			continue

		if (comonfilter != None and comonfilter in vals['comonstats'] and vals['comonstats'][comonfilter] != 'null'):
			continue

		if nodeonlyfilter != None:
			print vals['nodename']
			continue

		site_string = row['site_string']
		if site_string != prev_sitestring:
			print "<tr><td bgcolor=lightblue nowrap>" 
			print site_string
			print "</td>"
		else:
			print "<tr><td>&nbsp;</td>"

		prev_sitestring = site_string

			
		# convert uname values into a single kernel version string
		if 'kernel' in vals:
			kernel = vals['kernel'].split()
			if len(kernel) > 0:
				if kernel[0] == "Linux":
					vals['kernel'] = kernel[2]
				else:
					vals['ssherror'] = vals['kernel']
					vals['kernel'] = ""
		else:
			vals['ssherror'] = ""
			vals['kernel'] = ""
#			continue
		if 'model' in vals or 'protocol' in vals or 'portstatus' in vals:
			#vals['model'] = string.replace(vals['model']," ", "&nbsp;")
			#vals['protocol'] = vals['protocol'].replace(" ", "&nbsp;")
			if vals['model'] == None:
				vals['model'] = " "
			vals['model'] = string.replace(vals['model']," ", "_")
			vals['protocol'] = vals['protocol'].replace(" ", "_")
			ps = ""
			ports = vals['portstatus']
			lports = ports.keys()
			lports.sort()
			for port in lports:
				t = ports[port]
				if t != "closed":
					ps += "%s:&nbsp;%s<br>" % (port, ports[port])
			if ps == "":
				ps = "All_closed"
				
			vals['portstatus'] = ps

		if 'reboot' in vals:
			vals['reboot'] = "%s" % vals['reboot']
			vals['reboot'] = vals['reboot'].replace(" ", "_")

		if 'nodename' in vals:
			url = "<a href='https://www.planet-lab.org/db/nodes/index.php?nodepattern=%s'>%s</a>" % (vals['nodename'], vals['nodename'])
			vals['nodename'] = url

		try:
			str_fields = []
			count = 0
			for f in format_fields:
				str_fields.append(f % vals)
				count += 1
		except:
			print >>sys.stderr, vals

		s = fields_to_html(str_fields, vals)
		print s
			
		print "\n</tr>"

	if nodeonlyfilter == None:
		print "</table>"
		print "<table>"
	keys = categories.keys()
	keys.sort()
	for cat in keys:
		print "<tr>"
		print "<th nowrap align=left>Total %s</th>" % cat
		print "<td align=left>%s</td>" % categories[cat]
		print "</tr>"
	if nodeonlyfilter == None:
		print "</table>"



if __name__ == '__main__':
	import cgi
	import cgitb; 
	cgitb.enable()
	import sys

	form = cgi.FieldStorage()
	myfilter = None

	if form.has_key('site'):
		myfilter = form.getvalue("site")
	else:
		myfilter = None

	if form.has_key('category'):
		mycategory = form.getvalue("category")
	else:
		mycategory = None

	if form.has_key('state'):
		mystate = form.getvalue("state")
	else:
		mystate = None

	if form.has_key('comon'):
		mycomon = form.getvalue("comon")
	else:
		mycomon = None

	if form.has_key('nodeonly'):
		mynodeonly = form.getvalue("nodeonly")
	else:
		mynodeonly = None

	parser = OptionParser()
	parser.set_defaults(cmpdays=False, 
						comon="sshstatus", 
						fields="nodename,ping,ssh,pcu,category,state,comonstats,kernel,bootcd", 
						dbname="findbad", # -070724-1", 
						cmpping=False, 
						cmpdns=False, 
						cmploginbase=False, 
						cmpssh=False, 
						cmpcategory=False,
						cmpstate=False)
	parser.add_option("", "--fields",	dest="fields", help="")
	parser.add_option("", "--dbname",	dest="dbname", help="")
	parser.add_option("", "--days",		dest="cmpdays", action="store_true", help="")
	parser.add_option("", "--ping",		dest="cmpping", action="store_true", help="")
	parser.add_option("", "--dns",		dest="cmpdns", action="store_true", help="")
	parser.add_option("", "--ssh",		dest="cmpssh",	action="store_true", help="")
	parser.add_option("", "--loginbase",dest="cmploginbase",action="store_true", help="")
	parser.add_option("", "--category",	dest="cmpcategory", action="store_true", help="")
	parser.add_option("", "--kernel",	dest="cmpkernel", action="store_true", help="")
	parser.add_option("", "--state",	dest="cmpstate", action="store_true", help="")
	parser.add_option("", "--comon",	dest="comon", 	help="")
	config = config(parser)
	config.parse_args()
	print "Content-Type: text/html\r\n"
	if mynodeonly == None:
		print "<html><body>\n"
	if len(sys.argv) > 1:
		if sys.argv[1] == "ssherror":
			ssherror = True
	main(myfilter, mycategory, mystate, mycomon,mynodeonly)
	if mynodeonly == None:
		print "</body></html>\n"
