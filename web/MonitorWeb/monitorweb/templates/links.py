from monitor import config 
import urllib

def plc_node_uri(hostname):
	return "https://" + config.PLC_WWW_HOSTNAME + "/db/nodes/index.php?nodepattern=" + str(hostname)
def plc_site_uri(loginbase):
	return "https://" + config.PLC_WWW_HOSTNAME + "/db/sites/index.php?site_pattern=" + str(loginbase)
def plc_site_uri_id(site_id):
	return "https://" + config.PLC_WWW_HOSTNAME + "/db/sites/index.php?id=" + str(site_id)
def plc_pcu_uri_id(pcu_id):
	return "https://" + config.PLC_WWW_HOSTNAME + "/db/sites/pcu.php?id=" + str(pcu_id)


def query_to_path(**kwargs):
	args = []
	tgpath = ""
	tgparams = kwargs
	if tgparams:
		for key, value in tgparams.iteritems():
			if value is None:
				continue
			if isinstance(value, (list, tuple)):
				pairs = [(key, v) for v in value]
			else:
				pairs = [(key, value)]
			for k, v in pairs:
				if v is None:
					continue
				if isinstance(v, unicode):
					v = v.encode('utf8')
				args.append((k, str(v)))
	if args:
		query_string = urllib.urlencode(args, True)
		if '?' in tgpath:
			tgpath += '&' + query_string
		else:
			tgpath += '?' + query_string
	return tgpath

def link(base, ext=True, **kwargs):
	if ext:
		str = "?query=" + base + query_to_path(**kwargs)
	else:
		str = tg.url(base, **kwargs)
	#print "CREATED %s" % str
	return str
