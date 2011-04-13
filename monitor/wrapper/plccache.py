#!/usr/bin/python

import sys
from monitor.wrapper import plc
from monitor.generic import *
from monitor.database.info.model import *
from monitor import database
from monitor import config
import profile

l_sites = None
l_nodes = None
l_pcus = None

plcdb_hn2lb = None
plcdb_lb2hn = None
plcdb_id2lb = None

class CachedPLC(plc.PLC):

	def _param_to_str(self, name, *params):
		fields = len(params)
		retstr = ""
		retstr += "%s-" % name
		for x in params:
			retstr += "%s-" % x
		return retstr[:-1]

	def __getattr__(self, name):
		method = getattr(self.api, name)
		if method is None:
			raise AssertionError("method does not exist")

		def run_or_returncached(*params):
			cachename = self._param_to_str(name, *params)
			#print "cachename is %s" % cachename
			if hasattr(config, 'refresh'):
				refresh = config.refresh
			else:
				refresh = False

			if 'Get' in name:
				if not database.cachedRecently(cachename):
					load_old_cache = False
					try:
						values = method(self.auth, *params)
					except:
						print "Call %s FAILED: Using old cached data" % cachename
						load_old_cache = True

					if load_old_cache:
						values = database.dbLoad(cachename)
					else:
						database.dbDump(cachename, values)

					return values
				else:
					values = database.dbLoad(cachename)
					return values
			else:
				return method(self.auth, *params)

		return run_or_returncached

cacheapi = CachedPLC(plc.auth.auth, plc.auth.server)

def init():
	import traceback
	#print "IMPORTING PLCCACHE: ",
	#traceback.print_stack()
	global l_sites
	global l_nodes
	global l_pcus
	global plcdb_hn2lb
	global plcdb_lb2hn
	global plcdb_id2lb
	print >>sys.stderr, "initing plccache"

	print >>sys.stderr, "collecting plcsites"
	dbsites = PlcSite.query.all()
	l_sites = [ s.plc_site_stats for s in dbsites ]

	print >>sys.stderr, "collecting plcnodes"
	dbnodes = PlcNode.query.all()
	l_nodes = [ s.plc_node_stats for s in dbnodes ]

	print >>sys.stderr, "collecting plcpcus"
	dbpcus = PlcPCU2.query.all()
	l_pcus = []
	for s in dbpcus:
		pcu = {}
		for k in ['username', 'protocol', 'node_ids', 'ip', 
				  'pcu_id', 'hostname', 'site_id', 'notes', 
				  'model', 'password', 'ports']:
			pcu[k] = getattr(s, k)
		l_pcus.append(pcu)

	print >>sys.stderr, "building id2lb"
	(d_sites,id2lb) = dsites_from_lsites_id(l_sites)
	print >>sys.stderr, "building lb2hn"
	(plcdb, hn2lb, lb2hn, exclude) = dsn_from_dsln(d_sites, id2lb, l_nodes)

	plcdb_hn2lb = hn2lb
	plcdb_lb2hn = lb2hn
	plcdb_id2lb = id2lb

	l_nodes = filter(lambda x: x['hostname'] not in exclude, l_nodes)
	
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
	print "GetNodeByName %s" % hostname
	node = PlcNode.get_by(hostname=hostname)
	return node.plc_node_stats

def GetSitesByName(sitelist):
	ret = []
	for site in sitelist:
		site = PlcSite.get_by(loginbase=site)
		ret.append(site.plc_site_stats)
	return ret

def GetSitesById(idlist):
	ret = []
	for site_id in idlist:
		site = PlcSite.get_by(site_id=site_id)
		ret.append(site.plc_site_stats)
	return ret

def deleteExtra(l_plc, objectClass=PlcSite, dbKey='loginbase', plcKey='login_base'):
	dbobjs = objectClass.query.all()
	dbobj_key = [ getattr(s, dbKey) for s in dbobjs ]
	plcobj_key = [ s[plcKey] for s in l_plc ]
	extra_key = set(dbobj_key) - set(plcobj_key)
	for obj in extra_key:
		print >>sys.stderr, "deleting %s" % obj
		dbobj = objectClass.get_by(**{dbKey : obj})
		dbobj.delete()

def conv(s):
    # strip non-ascii characters to prvent errors
    r = s
    if type(s) in (str,unicode):
        r = "".join([x for x in s if ord(x) < 128])
    return r

def sync():
	l_sites = plc.api.GetSites({'peer_id':None}, 
						['login_base', 'site_id', 'abbreviated_name', 'latitude', 
						'longitude', 'max_slices', 'slice_ids', 'node_ids', 
						'enabled', 'date_created' ])
	l_nodes = plc.api.GetNodes({'peer_id':None}, 
						['hostname', 'node_id', 'ports', 'site_id', 'boot_state', 'run_level',
						 'version', 'last_updated', 'date_created', 'key',
						 'last_contact', 'pcu_ids', 'interface_ids'])
	l_pcus = plc.api.GetPCUs()

	print >>sys.stderr, "sync sites"
	for site in l_sites:
		dbsite = PlcSite.findby_or_create(site_id=site['site_id'])
		dbsite.loginbase = site['login_base']
		dbsite.date_checked = datetime.now()
		dbsite.plc_site_stats = site
	deleteExtra(l_sites, PlcSite, 'loginbase', 'login_base')
	deleteExtra(l_sites, HistorySiteRecord, 'loginbase', 'login_base')
	session.flush()

	print >>sys.stderr, "sync pcus"
	for pcu in l_pcus:
		dbpcu = PlcPCU2.findby_or_create(pcu_id=pcu['pcu_id'])
		dbpcu.date_checked = datetime.now()
		for key in pcu.keys():
			print >>sys.stderr, "setting %s  = %s" % (key, conv(pcu[key]))
			setattr(dbpcu, key, conv(pcu[key]))

	deleteExtra(l_pcus, PlcPCU2, 'pcu_id', 'pcu_id')
	deleteExtra(l_pcus, HistoryPCURecord, 'plc_pcuid', 'pcu_id')
	deleteExtra(l_pcus, FindbadPCURecord, 'plc_pcuid', 'pcu_id')
	session.flush()

	print >>sys.stderr, "sync nodes"
	for node in l_nodes:
		dbnode = PlcNode.findby_or_create(node_id=node['node_id'])
		dbnode.hostname = node['hostname']
		dbnode.date_checked = datetime.now()
		dbnode.plc_node_stats = node
	deleteExtra(l_nodes, PlcNode, 'node_id', 'node_id')
	deleteExtra(l_nodes, HistoryNodeRecord, 'plc_nodeid', 'node_id')
        deleteExtra(l_nodes, PlcNode, 'hostname', 'hostname')
	deleteExtra(l_nodes, HistoryNodeRecord, 'hostname', 'hostname')
	deleteExtra(l_nodes, FindbadNodeRecord, 'hostname', 'hostname')
	session.flush()

	init()

	return

if __name__ == '__main__':
	sync()
else:
	init()
