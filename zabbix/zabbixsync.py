#!/usr/bin/python

import sys
import site
from monitor.wrapper import plc
from monitor import database

import zabbixsite
from monitor.database.dborm import session

print "test"

plcdb = database.dbLoad("l_plcsites")
netid2ip = database.dbLoad("plcdb_netid2ip")
lb2hn = database.dbLoad("plcdb_lb2hn")

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
	#sites = api.GetSites({'peer_id' : None}, ['login_base'])
	for loginbase in ['princeton', 'princetondsl', 'monitorsite']:
		add_loginbase(loginbase)

	session.flush()

## Scripts : includes external scripts to: 
#		  - reboot.py
#		  - nmap

## UserGroups
# define technical contact, principal investigator groups
# define a Group for every site

## Users
# define a User for every user with admin/tech/pi roles
# 		get passwords from a combination of site&name, perhaps?
#		I'm guessing we could use the grpid or userid as part of the passwd,
#		so that it varies in general, and can be guessed from the templates
# add user to groups

## Discovery Rules and Actions
# define a discovery rule for every site's hosts.
# define discovery action for online hosts.

## Messages & Escalations
# define actions and escellations for trigger sources:
#		- unreachable host,

## HostGroups
# add host group for every site
# add host group for global network (PLC name)

## Hosts & Templates
# no need to define hosts?
# add template?  It appears that the xml-based tempate system is sufficient.
