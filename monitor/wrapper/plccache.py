#!/usr/bin/python

import sys
from monitor.wrapper import plc
from monitor.database.info.model import *

def dsites_from_lsites(l_sites):
	d_sites = {}
	id2lb = {}
	for site in l_sites:
		if not site['login_base'] in d_sites:
			d_sites[site['login_base']] = site
			id2lb[site['site_id']] = site['login_base']
		else:
			#print "Two sites have the same login_base value %s!" % site['login_base']
			#sys.exit(1)
			continue
	return (d_sites, id2lb)

def dsn_from_dsln(d_sites, id2lb, l_nodes):
	lb2hn = {}
	dsn = {}
	hn2lb = {}
	for id in id2lb:
		if id2lb[id] not in lb2hn:
			lb2hn[id2lb[id]] = []

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

l_sites = None
l_nodes = None
l_pcus = None

plcdb_hn2lb = None
plcdb_lb2hn = None
plcdb_id2lb = None

def init():
	global l_sites
	global l_nodes
	global l_pcus
	global plcdb_hn2lb
	global plcdb_lb2hn
	global plcdb_id2lb

	dbsites = PlcSite.query.all()
	l_sites = [ s.plc_site_stats for s in dbsites ]

	dbnodes = PlcNode.query.all()
	l_nodes = [ s.plc_node_stats for s in dbnodes ]

	dbpcus = PlcPCU.query.all()
	l_pcus = [ s.plc_pcu_stats for s in dbpcus ]

	(d_sites,id2lb) = dsites_from_lsites(l_sites)
	(plcdb, hn2lb, lb2hn) = dsn_from_dsln(d_sites, id2lb, l_nodes)

	plcdb_hn2lb = hn2lb
	plcdb_lb2hn = lb2hn
	plcdb_id2lb = id2lb
	
	return

def GetNodesByIds(ids):
	ret = []
	for node_id in ids:
		node = PlcNode.get_by(node_id=node_id)
		ret.append(node.plc_node_stats)
	return ret

def GetNodesBySite(loginbase):
	site = PlcSite.get_by(loginbase=loginbase)
	return GetNodesByIds(site.plc_site_stats['node_ids'])

def GetNodeByName(hostname):
	node = PlcNode.get_by(hostname=hostname)
	return node.plc_node_stats

def GetSitesByName(sitelist):
	ret = []
	for site in sitelist:
		site = PlcSite.get_by(loginbase=site)
		ret.append(site.plc_site_stats)
	return ret

def sync():
	l_sites = plc.api.GetSites({'peer_id':None}, 
						['login_base', 'site_id', 'abbreviated_name', 'latitude', 
						'longitude', 'max_slices', 'slice_ids', 'node_ids', 
						'enabled', 'date_created' ])
	l_nodes = plc.api.GetNodes({'peer_id':None}, 
						['hostname', 'node_id', 'ports', 'site_id', 
						 'version', 'last_updated', 'date_created', 
						 'last_contact', 'pcu_ids', 'nodenetwork_ids'])
	l_pcus = plc.api.GetPCUs()

	print "sync sites"
	for site in l_sites:
		dbsite = PlcSite.findby_or_create(site_id=site['site_id'])
		dbsite.loginbase = site['login_base']
		dbsite.date_checked = datetime.now()
		dbsite.plc_site_stats = site
		#dbsite.flush()
	# TODO: delete old records.
	session.flush()

	print "sync nodes"
	for node in l_nodes:
		dbnode = PlcNode.findby_or_create(node_id=node['node_id'])
		dbnode.hostname = node['hostname']
		dbnode.date_checked = datetime.now()
		dbnode.plc_node_stats = node
		#dbnode.flush()
	# TODO: delete old records.
	session.flush()

	print "sync pcus"
	for pcu in l_pcus:
		dbpcu = PlcPCU.findby_or_create(pcu_id=pcu['pcu_id'])
		dbpcu.date_checked = datetime.now()
		dbpcu.plc_pcu_stats = pcu
		#dbpcu.flush()
	# TODO: delete old records.
	session.flush()

	init()

	return

if __name__ == '__main__':
	sync()
else:
	init()
