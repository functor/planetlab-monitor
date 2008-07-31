#!/usr/bin/python

import plc
from config import config
import soltesz
import sys

config = config()

def dsites_from_lsites(l_sites):
	d_sites = {}
	id2lb = {}
	for site in l_sites:
		if not site['login_base'] in d_sites:
			d_sites[site['login_base']] = site
			id2lb[site['site_id']] = site['login_base']
		else:
			#print "Two sites have the same login_base value %s!" % site['login_base']
			sys.exit(1)
	return (d_sites, id2lb)

def dsn_from_dsln(d_sites, id2lb, l_nodes):
	lb2hn = {}
	dsn = {}
	hn2lb = {}
	for node in l_nodes:
		# this won't reach sites without nodes, which I guess isn't a problem.
		if node['site_id'] in id2lb.keys():
			login_base = id2lb[node['site_id']]
		else:
			print "%s has a foreign site_id %s" % (node['hostname'], 
													node['site_id'])
			continue
			for i in id2lb:
				print i, " ", id2lb[i]
			raise Exception, "Node has missing site id!! %s %d" %(node['hostname'], node['site_id'])
		if not login_base in dsn:
			lb2hn[login_base] = []
			dsn[login_base] = {}
			dsn[login_base]['plc'] = d_sites[login_base]
			dsn[login_base]['monitor'] = {} # event log, or something

		hostname = node['hostname']
		lb2hn[login_base].append(node)
		dsn[login_base][hostname] = {}
		dsn[login_base][hostname]['plc'] = node
		dsn[login_base][hostname]['comon'] = {}
		dsn[login_base][hostname]['monitor'] = {}

		hn2lb[hostname] = login_base
	return (dsn, hn2lb, lb2hn)

def create_netid2ip(l_nodes, l_nodenetworks):
	netid2ip = {}
	for node in l_nodes:
		for netid in node['nodenetwork_ids']:
			found = False
			for nn in l_nodenetworks:
				if nn['nodenetwork_id'] == netid:
					found = True
					netid2ip[netid] = nn['ip']
			if not found:
				print "ERROR! %s" % node

	return netid2ip

def create_plcdb():

	# get sites, and stats
	l_sites = plc.getSites({'peer_id':None}, ['login_base', 'site_id', 'abbreviated_name', 'latitude', 'longitude', 
											  'max_slices', 'slice_ids', 'node_ids' ])
	if len(l_sites) == 0:
		sys.exit(1)
	(d_sites,id2lb) = dsites_from_lsites(l_sites)

	# get nodes at each site, and 
	l_nodes = plc.getNodes({'peer_id':None}, ['hostname', 'node_id', 'ports', 'site_id', 'version', 
	                                          'last_updated', 'date_created', 'last_contact', 'pcu_ids', 'nodenetwork_ids'])

	l_nodenetworks = plc.getNodeNetworks()
	(plcdb, hn2lb, lb2hn) = dsn_from_dsln(d_sites, id2lb, l_nodes)
	netid2ip = create_netid2ip(l_nodes, l_nodenetworks)

	# save information for future.
	id2lb = id2lb
	hn2lb = hn2lb
	db = plcdb

	if ('cachenodes' in dir(config) and config.cachenodes) or \
		'cachenodes' not in dir(config):
		soltesz.dbDump("plcdb_hn2lb", hn2lb)
		soltesz.dbDump("plcdb_lb2hn", lb2hn)
		soltesz.dbDump("plcdb_netid2ip", netid2ip)
		soltesz.dbDump("l_plcnodenetworks", l_nodenetworks)
		soltesz.dbDump("l_plcnodes", l_nodes)
		soltesz.dbDump("l_plcsites", l_sites)
	
	return l_nodes
	

if __name__ == '__main__':
	create_plcdb()
