#!/usr/bin/python

import sys
import site
from monitor.wrapper import plc, plccache
from monitor import database

import zabbixsite
from monitor.database.dborm import zab_session as session


plcdb = plccache.l_sites # database.dbLoad("l_plcsites")
netid2ip = plccache.plcdb_netid2ip # database.dbLoad("plcdb_netid2ip")
lb2hn = plccache.plcdb_lb2hn # database.dbLoad("plcdb_lb2hn")

def get_site_iplist(loginbase):
	node_list = lb2hn[loginbase]

	# TODO: ip_list string cannot be longer than 255 characters.
	# TODO: if it is, then we need to break up the discovery rule.
	ip_list = ""
	for node in node_list:
		ip = netid2ip[node['nodenetwork_ids'][0]]
		if len(ip_list) > 0: ip_list += ","
		ip_list += ip

	return ip_list
	
def add_loginbase(loginbase):
	
	techs = plc.getTechEmails(loginbase)
	pis = plc.getPIEmails(loginbase)
	iplist = get_site_iplist(loginbase)

	print "zabbixsite.setup_site('%s', %s, %s, '%s')" % (loginbase,techs, pis, iplist)
	zabbixsite.setup_site(loginbase, techs, pis, iplist)

if __name__=="__main__":

	from monitor import parser as parsermodule
	parser = parsermodule.getParser(['cacheset'])
	parser.set_defaults( setupglobal=False, syncsite=True, site=None)
	parser.add_option("", "--setupglobal", action="store_true", dest="setupglobal",
						help="Setup global settings.")
	parser.add_option("", "--nosite", action="store_false", dest="syncsite",
						help="Do not sync sites.")
	parser.add_option("", "--site", dest="site",
						help="Sync only given site name.")
	opts = parsermodule.parse_args(parser)

	if opts.setupglobal:
		zabbixsite.setup_global()
		session.flush()

	if opts.syncsite:
		api = plc.getCachedAuthAPI()
		query = {'peer_id' : None}
		if opts.site:
			query.update({'login_base' : opts.site})

		sites = api.GetSites(query, ['login_base'])
		for site in sites:
			add_loginbase(site['login_base'])
			session.flush()

	# TODO: for any removed site that is in the db, call zabbixsite.delete_site()

