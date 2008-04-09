#!/usr/bin/python
import soltesz
from config import config
from optparse import OptionParser
from www.printbadnodes import *

def main():
	global fb
	db = soltesz.dbLoad(config.dbname)
	fb = soltesz.dbLoad("findbadpcus")
	act= soltesz.dbLoad("act_all")

	## Field widths used for printing
	maxFieldLengths = { 'nodename' : -45,
						'ping' : 6, 
						'ssh' : 6, 
						'rt' : 10, 
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
	if config.display:
		l_nodes = sys.argv[2:]
	else:
		l_nodes = d_n.keys()

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

		if 'pcu' in vals and vals['pcu'] == "PCU":
			# check the health of the pcu.
			s = pcu_state(vals['plcnode']['pcu_ids'][0])
			if s == 0:
				vals['pcu'] = "UP-PCU"
			else:
				vals['pcu'] = "DN-PCU"

		vals['rt'] = " -"
		if vals['nodename'] in act:
			if len(act[vals['nodename']]) > 0 and 'rt' in act[vals['nodename']][0]:
				if 'Status' in act[vals['nodename']][0]['rt']:
					vals['rt'] = "%s %s" % (act[vals['nodename']][0]['rt']['Status'], 
											act[vals['nodename']][0]['rt']['id'])

		str = format % vals 
		fields = str.split()
		#print "<tr>"
		s = fields_to_html(fields, vals)
		s = ""
		if config.display:
			print str

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
						fields="nodename,ping,ssh,pcu,category,state,kernel,bootcd,rt", 
						dbname="findbad", # -070724-1", 
						display=False,
						cmpping=False, 
						cmpssh=False, 
						cmpcategory=False,
						cmpstate=False)
	parser.add_option("", "--fields",	dest="dbname", help="")
	parser.add_option("", "--dbname",	dest="dbname", help="")
	parser.add_option("", "--display",	dest="display", action="store_true")
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
