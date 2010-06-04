#!/usr/bin/python
from nagiosobjects import *

command_auto = Command(command_name="automate-host-reboot-command",
				 	   command_line="""/usr/share/monitor/commands/reboot.py $NOTIFICATIONTYPE$ $HOSTNAME$""")

contact_auto = Contact(contact_name="automate-host-reboot-contact",
						host_notifications_enabled=1,
						service_notifications_enabled=0,
						host_notification_period="24x7",
						host_notification_options="d,r",
						host_notification_commands="automate-host-reboot-command",
						service_notification_period="24x7",
						service_notification_commands="monitor-notify-service-by-email",
						email="not.an.email")

print command_auto.toString()
print contact_auto.toString()

globalservices = []
for service in [('NET', "Network Services"),
				('SSH', "SSH Service"),
				('SSH806', "Auxiliary SSH Service"),
				('HTTP', "PlanetFlow HTTP"),
				('COTOP', "HTTP based COTOP"),
				]:
				#('PLSOFT', "PlanetLab Software"),
				#('MGMT',  "Remote Management")]:
	globalservices.append(ServiceGroup(servicegroup_name=service[0], alias=service[1]))


# NOTE: since ping is not a reliable check in the wide area, use 'check_ssh'
# 		to determine if the host is minimally online.  If we cannot access
# 		port 22 it, then it is DOWN.

globalhost = [Host(	name="planetlab-host",
					use="generic-host",
					check_period="24x7",
					check_interval="120",
					retry_interval="10",
					max_check_attempts="6",
					check_command="check_ssh!-t 120",
					contact_groups="admins",
					register="0")]

for obj in globalhost + globalservices:
	print obj.toString()

from monitor.wrapper import plc
from monitor.generic import *

l_sites = plc.api.GetSites({'login_base' : ['asu', 'gmu']})
#l_sites = plc.api.GetSites([10243, 22, 10247, 138, 139, 10050, 10257, 18, 20, 
#							21, 10134, 24, 10138, 10141, 30, 31, 33, 10279, 41, 29, 10193, 10064, 81,
#							10194, 10067, 87, 10208, 10001, 233, 157, 10100, 10107])

node_ids = [ s['node_ids'] for s in l_sites ]
node_ids = [ map(str,n) for n in node_ids ] 
node_ids = [ ",".join(n) for n in node_ids ] 
node_ids = ",".join(node_ids)
node_ids = map(int, node_ids.split(","))

l_nodes = plc.api.GetNodes(node_ids)

(d_sites,id2lb) = dsites_from_lsites_id(l_sites)
(plcdb, hn2lb, lb2hn) = dsn_from_dsln(d_sites, id2lb, l_nodes)

netid2ip = d_from_l(plc.api.GetInterfaces(), 'interface_id')

for site in l_sites:
	shortname = site['abbreviated_name']
	lb = site['login_base']
	hg = HostGroup(hostgroup_name=lb, alias=shortname)
	lat = site['latitude']
	lon = site['longitude']
	lon_x = -1
	lat_y = -1
	if lat is not None and lon is not None:
		scale = 5
		lon_x = int(180 + lon) * scale
		lat_y = int(180 - (lat + 90)) * scale

	if site['login_base'] in lb2hn:
		nodes = lb2hn[site['login_base']]
	else:
		continue

	if len(nodes) == 0:
		continue

	print hg.toString()

	hostname_list = []
	for node in nodes:
		hn = node['hostname']
		if len(node['interface_ids']) == 0:
			continue

		ip = netid2ip[str(node['interface_ids'][0])]['ip']

		if lon_x is not -1 and lat_y is not -1:
			coords="%s,%s" % (lon_x, lat_y)
		else:
			coords="0,0"
			
		h = Host(use="planetlab-host",
				host_name=hn,
				alias=hn,
				address=ip,
				d2_coords=coords,
				statusmap_image="icon-system.png",
				hostgroups=lb)

		print h.toString()

		hostname_list.append(hn)
	
	# NOTE: use all hostnames at site to create HostEscalations for down-notices
	if len(hostname_list) > 0:

		hn_list = ",".join(hostname_list)
		# NOTE: always send notices to techs
		he1 = HostEscalation( host_name=hn_list,
						first_notification=3,
						last_notification=0,
						notification_interval=24*60*1,
						escalation_options="r,d",
						contact_groups="%s-techs" % lb)

		# NOTE: only send notices to PIs after a week. (2 prior notices) 
		he2 = HostEscalation( host_name=hn_list,
						first_notification=5,
						last_notification=0,
						notification_interval=24*60*1,
						escalation_options="r,d",
						contact_groups="%s-pis" % lb)

		# NOTE: send notices to Slice users after two weeks. (4 prior notices) 
		he3 = HostEscalation( host_name=hn_list,
						first_notification=7,
						last_notification=0,
						notification_interval=24*60*1,
						escalation_options="r,d",
						contact_groups="%s-sliceusers" % lb)

		for he in [he1, he2, he3]:
			print he.toString()

		he_reboot = HostEscalation(host_name=hn_list,
						first_notification=2,
						last_notification=2,
						notification_interval=24*60*0.5,
						escalation_options="d",
						contacts="automate-host-reboot-contact")

		print he_reboot.toString()


if len(hostname_list) > 0:
		hn = ",".join(hostname_list)

		s1 = Service(use="generic-service",
					host_name="*",
					service_description="aSSH",
					display_name="aSSH",
					servicegroups="NET,SSH",
					notifications_enabled="0",
					check_command="check_ssh!-t 120")
		s2 = Service(use="generic-service",
					host_name="*",
					service_description="bSSH806",
					display_name="bSSH806",
					servicegroups="NET,SSH806",
					notifications_enabled="0",
					check_command="check_ssh!-p 806 -t 120")
		s3 = Service(use="generic-service",
					host_name="*",
					service_description="cHTTP",
					display_name="cHTTP",
					servicegroups="NET,HTTP",
					notifications_enabled="0",
					check_command="check_http!-t 120")
		s4 = Service(use="generic-service",
					host_name="*",
					service_description="dCOTOP",
					display_name="dCOTOP",
					servicegroups="NET,COTOP",
					notifications_enabled="0",
					check_command="check_http!-p 3120 -t 120")




		sd1 = ServiceDependency(host_name="*",
								service_description="aSSH",
								dependent_service_description="bSSH806,cHTTP,dCOTOP",
								execution_failure_criteria="w,u,c,p",)

		for service in [s1,s2,s3,s4,sd1]:
			print service.toString()

