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
	dsn = {}
	hn2lb = {}
	for node in l_nodes:
		# this won't reach sites without nodes, which I guess isn't a problem.
		if node['site_id'] in id2lb.keys():
			login_base = id2lb[node['site_id']]
		else:
			for i in id2lb:
				print i, " ", id2lb[i]
			raise Exception, "Node has missing site id!! %s %d" %(node['hostname'], node['site_id'])
		if not login_base in dsn:
			dsn[login_base] = {}
			dsn[login_base]['plc'] = d_sites[login_base]
			dsn[login_base]['monitor'] = {} # event log, or something

		hostname = node['hostname']
		dsn[login_base][hostname] = {}
		dsn[login_base][hostname]['plc'] = node
		dsn[login_base][hostname]['comon'] = {}
		dsn[login_base][hostname]['monitor'] = {}

		hn2lb[hostname] = login_base
	return (dsn, hn2lb)

def create_plcdb():

	# get sites, and stats
	l_sites = plc.getSites({'peer_id':None}, ['login_base', 'site_id'])
	if len(l_sites) == 0:
		sys.exit(1)
	(d_sites,id2lb) = dsites_from_lsites(l_sites)

	# get nodes at each site, and 
	l_nodes = plc.getNodes({'peer_id':None}, ['hostname', 'site_id', 'version', 'last_updated', 'date_created', 'last_contact', 'pcu_ids'])
	(plcdb, hn2lb) = dsn_from_dsln(d_sites, id2lb, l_nodes)

	# save information for future.
	id2lb = id2lb
	hn2lb = hn2lb
	db = plcdb

	if config.cachenodes:
		soltesz.dbDump("plcdb_hn2lb", hn2lb)
		soltesz.dbDump("l_plcnodes", l_nodes)
		soltesz.dbDump("l_plcsites", l_sites)
	
	return l_nodes
	

if __name__ == '__main__':
	create_plcdb()
