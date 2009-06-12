#!/usr/bin/python

import sys
from nodecommon import *
import glob
import os
from monitor.util import file

import time
import re

#fb = {}
fb = None
fbpcu = None

class NoKeyException(Exception): pass

def fb_print_nodeinfo(fbnode, hostname, fields=None):
	fbnode['hostname'] = hostname
	fbnode['checked'] = diff_time(fbnode['checked'])
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	fbnode['pcu'] = color_pcu_state(fbnode)

	if not fields:
		if 'ERROR' in fbnode['category']:
			fbnode['kernel'] = ""
		else:
			fbnode['kernel'] = fbnode['kernel'].split()[2]
		fbnode['boot_state'] = fbnode['plcnode']['boot_state']

		try:
			if len(fbnode['nodegroups']) > 0:
				fbnode['category'] = fbnode['nodegroups'][0]
		except:
			#print "ERROR!!!!!!!!!!!!!!!!!!!!!"
			pass

		print "%(hostname)-45s | %(checked)11.11s | %(boot_state)5.5s| %(state)8.8s | %(ssh)5.5s | %(pcu)6.6s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode
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
					con_and_true = con_and_true & (value_re.search(data[key]) is not None)
			elif key not in data:
				print "missing key %s" % key,
				pass
				#print "missing key %s" % key
				#con_and_true = False

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
	
		fb_nodeinfo  = fb['nodes'][node]['values']

		if fb_nodeinfo == []:
			#print node, "has lost values"
			continue
			#sys.exit(1)
		#fb_nodeinfo['pcu'] = color_pcu_state(fb_nodeinfo)
		fb_nodeinfo['hostname'] = node
		if 'plcnode' in fb_nodeinfo:
			fb_nodeinfo.update(fb_nodeinfo['plcnode'])

		if verify(dict_query, fb_nodeinfo):
			#print node #fb_nodeinfo
			hostnames.append(node)
		else:
			#print "NO MATCH", node
			pass
	
	return hostnames

