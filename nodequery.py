#!/usr/bin/python


import sys
from monitor import database
from nodecommon import *
from monitor.model import Record
import glob
import os
import traceback

import time
import re
import string

from pcucontrol  import reboot
from monitor.wrapper import plc, plccache
api = plc.getAuthAPI()

from monitor.database.info.model import FindbadNodeRecordSync, FindbadNodeRecord, FindbadPCURecord, session
from monitor import util
from monitor import config


class NoKeyException(Exception): pass

def daysdown_print_nodeinfo(fbnode, hostname):
	fbnode['hostname'] = hostname
	fbnode['daysdown'] = Record.getStrDaysDown(fbnode)
	fbnode['intdaysdown'] = Record.getDaysDown(fbnode)

	print "%(intdaysdown)5s %(hostname)-44s | %(state)10.10s | %(daysdown)s" % fbnode

def fb_print_nodeinfo(fbnode, hostname, fields=None):
	#fbnode['hostname'] = hostname
	#fbnode['checked'] = diff_time(fbnode['checked'])
	if fbnode['bootcd_version']:
		fbnode['bootcd_version'] = fbnode['bootcd_version'].split()[-1]
	else:
		fbnode['bootcd_version'] = "unknown"
	fbnode['pcu'] = color_pcu_state(fbnode)

	if not fields:
		if ( fbnode['observed_status'] is not None and \
		   'DOWN' in fbnode['observed_status'] ) or \
		   fbnode['kernel_version'] is None:
			fbnode['kernel_version'] = ""
		else:
			fbnode['kernel_version'] = fbnode['kernel_version'].split()[2]

		if fbnode['plc_node_stats'] is not None:
			fbnode['boot_state'] = fbnode['plc_node_stats']['boot_state']
		else:
			fbnode['boot_state'] = "unknown"

		try:
			if len(fbnode['nodegroups']) > 0:
				fbnode['category'] = fbnode['nodegroups'][0]
		except:
			#print "ERROR!!!!!!!!!!!!!!!!!!!!!"
			pass

		print "%(hostname)-45s | %(date_checked)11.11s | %(boot_state)5.5s| %(observed_status)8.8s | %(ssh_status)5.5s | %(pcu)6.6s | %(bootcd_version)6.6s | %(kernel_version)s" % fbnode
	else:
		format = ""
		for f in fields:
			format += "%%(%s)s " % f
		print format % fbnode

def first(path):
	indexes = path.split(".")
	return indexes[0]
	
def get(fb, path):
    indexes = path.split(".")
    values = fb
    for index in indexes:
		if values and index in values:
			values = values[index]
		else:
			raise NoKeyException(index)
    return values

def verifyType(constraints, data):
	"""
		constraints is a list of key, value pairs.
		# [ {... : ...}==AND , ... , ... , ] == OR
	"""
	con_or_true = False
	for con in constraints:
		#print "con: %s" % con
		if len(con.keys()) == 0:
			con_and_true = False
		else:
			con_and_true = True

		for key in con.keys():
			#print "looking at key: %s" % key
			if data is None:
				con_and_true = False
				break

			try:
				get(data,key)
				o = con[key]
				if o.name() == "Match":
					if get(data,key) is not None:
						value_re = re.compile(o.value)
						con_and_true = con_and_true & (value_re.search(get(data,key)) is not None)
					else:
						con_and_true = False
				elif o.name() == "ListMatch":
					if get(data,key) is not None:
						match = False
						for listitem in get(data,key):
							value_re = re.compile(o.value)
							if value_re.search(listitem) is not None:
								match = True
								break
						con_and_true = con_and_true & match
					else:
						con_and_true = False
				elif o.name() == "Is":
					con_and_true = con_and_true & (get(data,key) == o.value)
				elif o.name() == "FilledIn":
					con_and_true = con_and_true & (len(get(data,key)) > 0)
				elif o.name() == "PortOpen":
					if get(data,key) is not None:
						v = get(data,key)
						con_and_true = con_and_true & (v[str(o.value)] == "open")
					else:
						con_and_true = False
				else:
					value_re = re.compile(o.value)
					con_and_true = con_and_true & (value_re.search(get(data,key)) is not None)

			except NoKeyException, key:
				print "missing key %s" % key,
				pass
				#print "missing key %s" % key
				#con_and_true = False

		con_or_true = con_or_true | con_and_true

	return con_or_true

def verifyDBrecord(constraints, record):
	"""
		constraints is a list of key, value pairs.
		# [ {... : ...}==AND , ... , ... , ] == OR
	"""
	def has_key(obj, key):
		try:
			x = obj.__getattribute__(key)
			return True
		except:
			return False

	def get_val(obj, key):
		try:
			return obj.__getattribute__(key)
		except:
			return None

	def get(obj, path):
		indexes = path.split("/")
		value = get_val(obj,indexes[0])
		if value is not None and len(indexes) > 1:
			for key in indexes[1:]:
				if key in value:
					value = value[key]
				else:
					raise NoKeyException(key)
		return value

	#print constraints, record

	con_or_true = False
	for con in constraints:
		#print "con: %s" % con
		if len(con.keys()) == 0:
			con_and_true = False
		else:
			con_and_true = True

		for key in con.keys():
			#print "looking at key: %s" % key
			if has_key(record, key):
				value_re = re.compile(con[key])
				if type([]) == type(get(record,key)):
					local_or_true = False
					for val in get(record,key):
						local_or_true = local_or_true | (value_re.search(val) is not None)
					con_and_true = con_and_true & local_or_true
				else:
					if get(record,key) is not None:
						con_and_true = con_and_true & (value_re.search(get(record,key)) is not None)
			else:
				print "missing key %s" % key,
				pass

		con_or_true = con_or_true | con_and_true

	return con_or_true

def verify(constraints, data):
	"""
		constraints is a list of key, value pairs.
		# [ {... : ...}==AND , ... , ... , ] == OR
	"""
	con_or_true = False
	for con in constraints:
		#print "con: %s" % con
		if len(con.keys()) == 0:
			con_and_true = False
		else:
			con_and_true = True

		for key in con.keys():
			#print "looking at key: %s" % key
			if first(key) in data: 
				value_re = re.compile(con[key])
				if type([]) == type(get(data,key)):
					local_or_true = False
					for val in get(data,key):
						local_or_true = local_or_true | (value_re.search(val) is not None)
					con_and_true = con_and_true & local_or_true
				else:
					if get(data,key) is not None:
						con_and_true = con_and_true & (value_re.search(get(data,key)) is not None)
			elif first(key) not in data:
				print "missing key %s" % first(key)

		con_or_true = con_or_true | con_and_true

	return con_or_true

def query_to_dict(query):
	
	ad = []

	or_queries = query.split('||')
	for or_query in or_queries:
	 	and_queries = or_query.split('&&')

		d = {}

		for and_query in and_queries:
			(key, value) = and_query.split('=')
			d[key] = value

		ad.append(d)
	
	return ad

def pcu_in(fbdata):
	#if 'plcnode' in fbdata:
	if 'plc_node_stats' in fbdata:
		if fbdata['plc_node_stats'] and 'pcu_ids' in fbdata['plc_node_stats']:
			if len(fbdata['plc_node_stats']['pcu_ids']) > 0:
				return True
	return False

def pcu_select(str_query, nodelist=None):
	pcunames = []
	nodenames = []
	if str_query is None: return (nodenames, pcunames)

	if True:
		fbquery = FindbadNodeRecord.get_all_latest()
		fb_nodelist = [ n.hostname for n in fbquery ]
	if True:
		fbpcuquery = FindbadPCURecord.get_all_latest()
		fbpcu_list = [ p.plc_pcuid for p in fbpcuquery ]

	dict_query = query_to_dict(str_query)
	print "dict_query", dict_query
	print 'length %s' % len(fbpcuquery.all())

	for pcurec in fbpcuquery:
		pcuinfo = pcurec.to_dict()
		if verify(dict_query, pcuinfo):
			#nodenames.append(noderec.hostname)
			#print 'appending %s' % pcuinfo['plc_pcuid']
			pcunames.append(pcuinfo['plc_pcuid'])

	#for noderec in fbquery:
	#	if nodelist is not None: 
	#		if noderec.hostname not in nodelist: continue
#	
#		fb_nodeinfo  = noderec.to_dict()
#		if pcu_in(fb_nodeinfo):
#			pcurec = FindbadPCURecord.get_latest_by(plc_pcuid=get(fb_nodeinfo, 
#													'plc_node_stats.pcu_ids')[0]).first()
#			if pcurec:
#				pcuinfo = pcurec.to_dict()
#				if verify(dict_query, pcuinfo):
#					nodenames.append(noderec.hostname)
#					pcunames.append(pcuinfo['plc_pcuid'])
	return (nodenames, pcunames)

def node_select(str_query, nodelist=None, fb=None):

	hostnames = []
	if str_query is None: return hostnames

	#print str_query
	dict_query = query_to_dict(str_query)
	#print dict_query

	for node in nodelist:
		#if nodelist is not None: 
		#	if node not in nodelist: continue

		try:
			fb_noderec = None
			#fb_noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==node).order_by(FindbadNodeRecord.date_checked.desc()).first()
			fb_noderec = FindbadNodeRecord.get_latest_by(hostname=node)
		except:
			print traceback.print_exc()
			continue

		if fb_noderec:
			fb_nodeinfo = fb_noderec.to_dict()

			#fb_nodeinfo['pcu'] = color_pcu_state(fb_nodeinfo)
			#if 'plcnode' in fb_nodeinfo:
			#	fb_nodeinfo.update(fb_nodeinfo['plcnode'])

			#if verifyDBrecord(dict_query, fb_nodeinfo):
			if verify(dict_query, fb_nodeinfo):
				#print fb_nodeinfo.keys()
				#print node #fb_nodeinfo
				hostnames.append(node)
			else:
				#print "NO MATCH", node
				pass
	
	return hostnames


def main():

	from monitor import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(node=None, fromtime=None, select=None, list=None, listkeys=False,
						pcuselect=None, nodelist=None, daysdown=None, fields=None)
	parser.add_option("", "--daysdown", dest="daysdown", action="store_true",
						help="List the node state and days down...")
	parser.add_option("", "--select", dest="select", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--fields", dest="fields", metavar="key,list,...", 
						help="a list of keys to display for each entry.")
	parser.add_option("", "--list", dest="list", action="store_true", 
						help="Write only the hostnames as output.")
	parser.add_option("", "--pcuselect", dest="pcuselect", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
						help="A list of nodes to bring out of debug mode.")
	parser.add_option("", "--listkeys", dest="listkeys", action="store_true",
						help="A list of nodes to bring out of debug mode.")
	parser.add_option("", "--fromtime", dest="fromtime", metavar="YYYY-MM-DD",
					help="Specify a starting date from which to begin the query.")

	parser = parsermodule.getParser(['defaults'], parser)
	config = parsermodule.parse_args(parser)
	
	if config.fromtime:
		path = "archive-pdb"
		archive = database.SPickle(path)
		d = datetime_fromstr(config.fromtime)
		glob_str = "%s*.production.findbad.pkl" % d.strftime("%Y-%m-%d")
		os.chdir(path)
		#print glob_str
		file = glob.glob(glob_str)[0]
		#print "loading %s" % file
		os.chdir("..")
		fb = archive.load(file[:-4])
	else:
		#fbnodes = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname, orderBy='date_checked',distinct=True).reversed()
		fb = None

	#reboot.fb = fbpcu

	if config.nodelist:
		nodelist = util.file.getListFromFile(config.nodelist)
	else:
		# NOTE: list of nodes should come from findbad db.   Otherwise, we
		# don't know for sure that there's a record in the db..
		plcnodes = plccache.l_nodes
		nodelist = [ node['hostname'] for node in plcnodes ]
		#nodelist = ['planetlab-1.cs.princeton.edu']

	pculist = None
	if config.select is not None and config.pcuselect is not None:
		nodelist = node_select(config.select, nodelist, fb)
		nodelist, pculist = pcu_select(config.pcuselect, nodelist)
	elif config.select is not None:
		nodelist = node_select(config.select, nodelist, fb)
	elif config.pcuselect is not None:
		nodelist, pculist = pcu_select(config.pcuselect, nodelist)

	if pculist:
		for pcu in pculist:
			print pcu

	for node in nodelist:
		config.node = node

		if node not in nodelist:
			continue

		try:
			# Find the most recent record
			fb_noderec = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname==node).order_by(FindbadNodeRecord.date_checked.desc()).first()
		except:
			print traceback.print_exc()
			pass

		if config.listkeys:
			fb_nodeinfo = fb_noderec.to_dict()
			print "Primary keys available in the findbad object:"
			for key in fb_nodeinfo.keys():
				print "\t",key
			sys.exit(0)
			

		if config.list:
			print node
		else:
			if config.daysdown:
				daysdown_print_nodeinfo(fb_nodeinfo, node)
			else:
				fb_nodeinfo = fb_noderec.to_dict()
				if config.select:
					if config.fields:
						fields = config.fields.split(",")
					else:
						fields = None

					fb_print_nodeinfo(fb_nodeinfo, node, fields)
				elif not config.select and 'state' in fb_nodeinfo:
					fb_print_nodeinfo(fb_nodeinfo, node)
				else:
					pass
		
if __name__ == "__main__":
	main()
