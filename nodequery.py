#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
fb = soltesz.dbLoad("findbad")
fbpcu = soltesz.dbLoad("findbadpcus")
from nodecommon import *
from policy import Diagnose

import time
import re



def daysdown_print_nodeinfo(fbnode, hostname):
	fbnode['hostname'] = hostname
	fbnode['daysdown'] = Diagnose.getStrDaysDown(fbnode)
	fbnode['intdaysdown'] = Diagnose.getDaysDown(fbnode)

	print "%(intdaysdown)5s %(hostname)-44s | %(state)10.10s | %(daysdown)s" % fbnode

def fb_print_nodeinfo(fbnode, hostname):
	fbnode['hostname'] = hostname
	fbnode['checked'] = diff_time(fbnode['checked'])
	if fbnode['bootcd']:
		fbnode['bootcd'] = fbnode['bootcd'].split()[-1]
	else:
		fbnode['bootcd'] = "unknown"
	if 'ERROR' in fbnode['category']:
		fbnode['kernel'] = ""
	else:
		fbnode['kernel'] = fbnode['kernel'].split()[2]
	fbnode['pcu'] = color_pcu_state(fbnode)
	print "%(hostname)-39s | %(checked)11.11s | %(state)10.10s | %(ssh)5.5s | %(pcu)6.6s | %(bootcd)6.6s | %(category)8.8s | %(kernel)s" % fbnode

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
				con_and_true = con_and_true & (value_re.search(data[key]) is not None)
			elif key not in data:
				print "missing key %s" % key
				con_and_true = False

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

def _pcu_in(fbdata):
	if 'plcnode' in fbdata:
		if 'pcu_ids' in fbdata['plcnode']:
			if len(fbdata['plcnode']['pcu_ids']) > 0:
				return True
	return False

def pcu_select(str_query):
	pcunames = []
	if str_query is None: return pcunames

	#print str_query
	dict_query = query_to_dict(str_query)
	#print dict_query

	for node in fb['nodes'].keys():
	
		fb_nodeinfo  = fb['nodes'][node]['values']
		if _pcu_in(fb_nodeinfo):
			pcuinfo = fbpcu['nodes']['id_%s' % fb_nodeinfo['plcnode']['pcu_ids'][0]]['values']
			if verify(dict_query, pcuinfo):
				pcunames.append(node)
	
	return pcunames

def node_select(str_query):
	hostnames = []
	if str_query is None: return hostnames

	#print str_query
	dict_query = query_to_dict(str_query)
	#print dict_query

	for node in fb['nodes'].keys():
	
		fb_nodeinfo  = fb['nodes'][node]['values']

		if verify(dict_query, fb_nodeinfo):
			#print node #fb_nodeinfo
			hostnames.append(node)
		else:
			#print "NO MATCH", node
			pass
	
	return hostnames


def main():
	from config import config
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(node=None, select=None, pcuselect=None, nodelist=None, daysdown=None)
	parser.add_option("", "--daysdown", dest="daysdown", action="store_true",
						help="List the node state and days down...")
	parser.add_option("", "--select", dest="select", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--pcuselect", dest="pcuselect", metavar="key=value", 
						help="List all nodes with the given key=value pattern")
	parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
						help="A list of nodes to bring out of debug mode.")
	config = config(parser)
	config.parse_args()

	if config.nodelist:
		nodelist = config.getListFromFile(config.nodelist)
	elif config.select is not None:
		nodelist = node_select(config.select)
	elif config.pcuselect is not None:
		nodelist = pcu_select(config.pcuselect)
	else:
		nodelist = fb['nodes'].keys()

	for node in nodelist:
		config.node = node

		if node not in fb['nodes']:
			continue

		fb_nodeinfo  = fb['nodes'][node]['values']

		if config.daysdown:
			daysdown_print_nodeinfo(fb_nodeinfo, node)
		else:
			if config.select:
				fb_print_nodeinfo(fb_nodeinfo, node)
			elif not config.select and 'state' in fb_nodeinfo:
				fb_print_nodeinfo(fb_nodeinfo, node)
			else:
				pass
		
if __name__ == "__main__":
	main()
