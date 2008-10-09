#!/usr/bin/python

import plc
api = plc.getAuthAPI()

import sys
import database
from nodecommon import *
#from policy import Diagnose
from unified_model import Record
import glob
import os
from reboot import pcu_name
import reboot
from monitor import util
import traceback

import time
import re

import config

from monitor.database import FindbadNodeRecord, FindbadNodeRecordSync
#from sqlobject import connectionForURI,sqlhub
#connection = connectionForURI(config.sqlobjecturi)
#sqlhub.processConnection = connection
#from infovacuum.model.findbadrecord import *

#fb = {}
fb = None
fbpcu = None
import string

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

def get(fb, path):
    indexes = path.split("/")
    values = fb
    for index in indexes:
        if index in values:
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
			if key in data: 
				value_re = re.compile(con[key])
				if type([]) == type(data[key]):
					local_or_true = False
					for val in data[key]:
						local_or_true = local_or_true | (value_re.search(val) is not None)
					con_and_true = con_and_true & local_or_true
				else:
					if data[key] is not None:
						con_and_true = con_and_true & (value_re.search(data[key]) is not None)
			elif key not in data:
				print "missing key %s" % key,
				pass

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
	if 'plcnode' in fbdata:
		if 'pcu_ids' in fbdata['plcnode']:
			if len(fbdata['plcnode']['pcu_ids']) > 0:
				return True
	return False

def pcu_select(str_query, nodelist=None):
	global fb
	global fbpcu
	pcunames = []
	nodenames = []
	if str_query is None: return (nodenames, pcunames)

	if fb is None:
		fb = database.dbLoad("findbad")
	if fbpcu is None:
		fbpcu = database.dbLoad("findbadpcus")

	#print str_query
	dict_query = query_to_dict(str_query)
	#print dict_query

	for node in fb['nodes'].keys():
		if nodelist is not None: 
			if node not in nodelist: continue
	
		fb_nodeinfo  = fb['nodes'][node]['values']
		if pcu_in(fb_nodeinfo):
			pcuinfo = fbpcu['nodes']['id_%s' % fb_nodeinfo['plcnode']['pcu_ids'][0]]['values']
			if verify(dict_query, pcuinfo):
				nodenames.append(node)
				str = "cmdhttps/locfg.pl -s %s -f iloxml/License.xml -u %s -p '%s' | grep MESSAGE" % \
							(pcu_name(pcuinfo), pcuinfo['username'], pcuinfo['password'])
				#pcunames.append(str)
				pcunames.append(pcuinfo['pcu_id'])
	return (nodenames, pcunames)

def node_select(str_query, nodelist=None, fbdb=None):
	global fb

	hostnames = []
	if str_query is None: return hostnames

	#print str_query
	dict_query = query_to_dict(str_query)
	#print dict_query

	if fbdb is not None:
		fb = fbdb

	for node in fb['nodes'].keys():
		if nodelist is not None: 
			if node not in nodelist: continue

		try:
			fb_noderec = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname==node, 
											   orderBy='date_checked').reversed()[0]
		except:
			continue

		
		fb_nodeinfo = fb_noderec.toDict()

		#fb_nodeinfo['pcu'] = color_pcu_state(fb_nodeinfo)
		#if 'plcnode' in fb_nodeinfo:
		#	fb_nodeinfo.update(fb_nodeinfo['plcnode'])

		#if verifyDBrecord(dict_query, fb_nodeinfo):
		if verify(dict_query, fb_nodeinfo):
			#print node #fb_nodeinfo
			hostnames.append(node)
		else:
			#print "NO MATCH", node
			pass
	
	return hostnames


def main():
	global fb
	global fbpcu

	import parser as parsermodule
	parser = parsermodule.getParser()

	parser.set_defaults(node=None, fromtime=None, select=None, list=None, 
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
		fbnodes = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname, orderBy='date_checked',distinct=True).reversed()
		fb = database.dbLoad("findbad")

	fbpcu = database.dbLoad("findbadpcus")
	reboot.fb = fbpcu

	if config.nodelist:
		nodelist = util.file.getListFromFile(config.nodelist)
	else:
		nodelist = fb['nodes'].keys()

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

		if node not in fb['nodes']:
			continue

		try:
			# Find the most recent record
			fb_noderec = FindbadNodeRecord.select(FindbadNodeRecord.q.hostname==node, 
											   orderBy='date_checked').reversed()[0]
		except:
			print traceback.print_exc()
			pass #fb_nodeinfo  = fb['nodes'][node]['values']

		if config.list:
			print node
		else:
			if config.daysdown:
				daysdown_print_nodeinfo(fb_nodeinfo, node)
			else:
				fb_nodeinfo = fb_noderec.toDict()
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
