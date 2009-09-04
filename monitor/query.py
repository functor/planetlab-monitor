#!/usr/bin/python

import os
import re
import sys
import glob
import time
import string
import traceback

from monitor.common import *
from monitor.database.info.model import FindbadNodeRecord, FindbadPCURecord

class NoKeyException(Exception): pass

def first(path):
	indexes = path.split(".")
	return indexes[0]
	
def get(fb, path):
    indexes = path.split(".")
    values = fb
    for index in indexes:
		if values and index in values:
			values = values[index]
		elif values == {}:
			values = ""
		else:
			print values, index
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
		# NOTE: this doesn't work when there are only a few records current.
		# pcu_select should apply to all pcus globally, not just the most recent records.
		fbpcuquery = FindbadPCURecord.get_all_latest()
		fbpcu_list = [ p.plc_pcuid for p in fbpcuquery ]

	dict_query = query_to_dict(str_query)
	print "dict_query", dict_query
	print 'length %s' % len(fbpcuquery)

	#for pcurec in fbpcuquery:
	#	pcuinfo = pcurec.to_dict()
	#	if verify(dict_query, pcuinfo):
	#		#nodenames.append(noderec.hostname)
	#		#print 'appending %s' % pcuinfo['plc_pcuid']
	#		pcunames.append(pcuinfo['plc_pcuid'])

	for noderec in fbquery:
		if nodelist is not None: 
			if noderec.hostname not in nodelist: continue
	
		fb_nodeinfo  = noderec.to_dict()
		if pcu_in(fb_nodeinfo):
			pcu_id = get(fb_nodeinfo, 'plc_node_stats.pcu_ids')[0]
			pcurec = FindbadPCURecord.get_by(plc_pcuid=pcu_id)

			if pcurec:
				pcuinfo = pcurec.to_dict()
				if verify(dict_query, pcuinfo):
					nodenames.append(noderec.hostname)
					pcunames.append(pcuinfo['plc_pcuid'])

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
		except KeyboardInterrupt:
			print "Exiting at user request: Ctrl-C"
			sys.exit(1)
		except:
			print traceback.print_exc()
			continue

		if fb_noderec:
			fb_nodeinfo = fb_noderec.to_dict()

			#fb_nodeinfo['pcu'] = color_pcu_state(fb_nodeinfo)
			#if 'plcnode' in fb_nodeinfo:
			#	fb_nodeinfo.update(fb_nodeinfo['plcnode'])

			if verify(dict_query, fb_nodeinfo):
				#print fb_nodeinfo.keys()
				#print node #fb_nodeinfo
				hostnames.append(node)
			else:
				#print "NO MATCH", node
				pass
	
	return hostnames


