#!/usr/bin/python
import soltesz
from config import config
from optparse import OptionParser
from printbadbysite import *


def main():
	db = soltesz.dbLoad(config.dbname)

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
	for f in config.fields.split(','):
		fields[f] = "%%(%s)%ds" % (f, maxFieldLengths[f])
	for f in config.fields.split(','):
		format += fields[f] + " "


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
	for nodename in l_nodes: 
		vals=d_n[nodename]['values'] 
		v = {}
		v.update(vals)
		v['nodename'] = nodename 
		if 'plcsite' in vals and 'status' in vals['plcsite'] and vals['plcsite']['status'] == "SUCCESS":
			site_string = "<b>%-20s</b> %2s nodes :: %2s of %4s slices" % ( \
														vals['plcsite']['login_base'],
														vals['plcsite']['num_nodes'], 
														vals['plcsite']['num_slices'], 
														vals['plcsite']['max_slices'])
			v['site_string'] = site_string
			d2.append(v)
		else:
			#print "ERROR: ", nodename, vals, "<br>"
			pass
			#site_string = "<b>UNKNOWN</b>"
			

	if config.cmpping:
		d2.sort(cmp=cmpPing)
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
	

	for row in d2:
		site_string = row['site_string']
		vals = row
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
			continue

		str = format % vals 
		fields = str.split()
		#print "<tr>"
		s = fields_to_html(fields, vals)

	keys = categories.keys()
	for cat in ['BOOT-ALPHA', 'BOOT-PROD', 'BOOT-OLDBOOTCD', 'DEBUG-ALPHA',
	'DEBUG-PROD', 'DEBUG-OLDBOOTCD', 'DOWN-ERROR']:
		if cat not in keys:
			categories[cat] = 0
	keys = categories.keys()
	for cat in ['BOOT-ALPHA', 'BOOT-PROD', 'BOOT-OLDBOOTCD', 'DEBUG-ALPHA',
	'DEBUG-PROD', 'DEBUG-OLDBOOTCD', 'DOWN-ERROR']:
		if cat in keys:
			print "%d," % categories[cat],
	print ""
import cgi
if __name__ == '__main__':
	parser = OptionParser()
	parser.set_defaults(cmpdays=False, 
						comon="sshstatus", 
						fields="nodename,ping,ssh,pcu,category,state,kernel,bootcd", 
						dbname="findbad", # -070724-1", 
						cmpping=False, 
						cmpssh=False, 
						cmpcategory=False,
						cmpstate=False)
	parser.add_option("", "--fields",	dest="dbname", help="")
	parser.add_option("", "--dbname",	dest="dbname", help="")
	parser.add_option("", "--days",		dest="cmpdays", action="store_true", help="")
	parser.add_option("", "--ping",		dest="cmpping", action="store_true", help="")
	parser.add_option("", "--ssh",		dest="cmpssh",	action="store_true", help="")
	parser.add_option("", "--category",	dest="cmpcategory", action="store_true", help="")
	parser.add_option("", "--kernel",	dest="cmpkernel", action="store_true", help="")
	parser.add_option("", "--state",	dest="cmpstate", action="store_true", help="")
	parser.add_option("", "--comon",	dest="comon", 	help="")
	config = config(parser)
	config.parse_args()
	main()
