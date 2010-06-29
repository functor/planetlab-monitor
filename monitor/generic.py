import sys
from datetime import datetime, timedelta

def d_from_l(l, key, using=None, key_as=str, using_as=None):
	d = {}
	for obj in l:
		if not str(obj[key]) in d:
			if using is None:
				d[key_as(obj[key])] = obj
			else:
				if using_as is None:
					d[key_as(obj[key])] = obj[using]
				else:
					d[key_as(obj[key])] = using_as(obj[using])
		else:
			print "Two objects have the same %s key %s!" % (key, obj[key])
			continue
	return d

def dpcus_from_lpcus(l_pcus):
	d_pcus = d_from_l(l_pcus, 'pcu_id')
	return d_pcus

def dnodes_from_lnodes(l_nodes):
	d_nodes = d_from_l(l_nodes, 'hostname')
	return d_nodes

def dsites_from_lsites(l_sites):
	d_sites = d_from_l(l_sites, 'login_base')
	return d_sites 

def dsites_from_lsites_id(l_sites):
	d_sites = d_from_l(l_sites, 'login_base')
	id2lb = d_from_l(l_sites, 'site_id', 'login_base', int, str)
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
			print >>sys.stderr, "%s has a foreign site_id %s" % (node['hostname'], node['site_id'])
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


class Time:
    @classmethod
    def dt_to_ts(cls, dt):
        t = time.mktime(dt.timetuple())
        return t

    @classmethod
    def ts_to_dt(cls, ts):
        d = datetime.fromtimestamp(ts)
        return d

    @classmethod
    def str_to_dt(cls, date_str, format="%Y-%m-%d %H:%M:%S"):
        dt = datetime.strptime(date_str[:date_str.find('.')], format)
        return dt

    @classmethod
    def str_to_ts(cls, date_str, format="%Y-%m-%d %H:%M:%S"):
        ts = time.mktime(time.strptime(date_str[:date_str.find('.')], format))
        return ts 
