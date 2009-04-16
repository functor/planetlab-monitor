#!/usr/bin/python

import sys
import os
import site
from monitor.wrapper import plc, plccache
from monitor import database

import zabbixsite
from monitor.database.dborm import zab_session as session
from monitor.database.zabbixapi.model import confirm_ids, HostGroup


plcdb = plccache.l_sites # database.dbLoad("l_plcsites")
netid2ip = plccache.plcdb_netid2ip # database.dbLoad("plcdb_netid2ip")
lb2hn = plccache.plcdb_lb2hn # database.dbLoad("plcdb_lb2hn")

def get_site_iplist(loginbase):
	node_list = lb2hn[loginbase]

	# TODO: ip_list string cannot be longer than 255 characters.
	# TODO: if it is, then we need to break up the discovery rule.
	ip_list = ""
	for node in node_list:
		if len(node['nodenetwork_ids']) > 0:
			ip = netid2ip[node['nodenetwork_ids'][0]]
			if len(ip_list) > 0: ip_list += ","
			ip_list += ip

	return ip_list
	
def add_loginbase(loginbase):
	
	techs = plc.getTechEmails(loginbase)
	pis = plc.getPIEmails(loginbase)
	iplist = get_site_iplist(loginbase)

	os.system("""echo '%s' | tr ',' '\n' >> /usr/share/monitor/nodelist.txt""" % iplist )

	print "zabbixsite.setup_site('%s', %s, %s, '%s')" % (loginbase,techs, pis, iplist)
	zabbixsite.setup_site(loginbase, techs, pis, iplist)

if __name__=="__main__":

	from monitor import parser as parsermodule
	parser = parsermodule.getParser(['cacheset'])
	parser.set_defaults( setupglobal=False, syncsite=True, site=None, sitelist=None, setupids=False)
	parser.add_option("", "--setupids", action="store_true", dest="setupids",
						help="Setup global IDs.")
	parser.add_option("", "--setupglobal", action="store_true", dest="setupglobal",
						help="Setup global settings.")
	parser.add_option("", "--nosite", action="store_false", dest="syncsite",
						help="Do not sync sites.")
	parser.add_option("", "--site", dest="site",
						help="Sync only given site name.")
	parser.add_option("", "--sitelist", dest="sitelist",
						help="Sync only given site names in the list.")
	opts = parsermodule.parse_args(parser)

	os.system("""echo '' > /usr/share/monitor/nodelist.txt""")

	if opts.setupids:
		# Not sure why, but this doesn't work if we continue.  so exit.
		# This step only needs to be called once, but there is no harm in
		# calling it multiple times.
		confirm_ids()
		session.flush()
		sys.exit(0)

	if opts.setupglobal:
		zabbixsite.setup_global()
		session.flush()

	if opts.syncsite:
		api = plc.getCachedAuthAPI()
		query = {'peer_id' : None}
		if opts.site:
			query.update({'login_base' : opts.site})

		# ADD SITES
		sites = api.GetSites(query, ['login_base'])
		site_api_list = [ site['login_base'] for site in sites ]
		for site in sites: # [:20]:
			add_loginbase(site['login_base'])
			session.flush()

		if not opts.site:
			# NOTE: for all sites in DB but not API, call zabbixsite.delete_site()
			hg_list = filter(lambda x: '_hostgroup' in x.name, HostGroup.query.all() )
			site_db_list = [ hg.name[:-len('_hostgroup')] for hg in hg_list ]
			in_db_not_plc = set(site_db_list) - set(site_api_list)
			for login_base in in_db_not_plc:
				print "Deleting %s" % login_base
				zabbixsite.delete_site(site['login_base'])


