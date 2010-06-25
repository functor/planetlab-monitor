#!/usr/bin/python

import plc
from nagiosobjects import *
from generic import *

command_auto = Command(command_name="check_mode",
				 	   command_line="""/usr/share/monitor/nagios/plugins/checkmode.py -H $HOSTNAME$ --sn $SERVICENOTIFICATIONNUMBER$ """)
print command_auto.toString()

command_auto = Command(command_name="check_pcu",
				 	   command_line="""/usr/share/monitor/nagios/plugins/checkpcu.py -H $HOSTNAME$ """)
print command_auto.toString()


command_auto = Command(command_name="automate-policy-escalation-command",
				 	   command_line="""/usr/share/monitor/nagios/actions/escalation.py $HOSTNAME$ $HOSTNOTIFICATIONNUMBER$ $HOSTDURATIONSEC$ $NOTIFICATIONTYPE$ """)
contact_auto = Contact(contact_name="automate-policy-escalation-contact",
						host_notifications_enabled=1,
						service_notifications_enabled=0,
						host_notification_period="24x7",
						host_notification_options="d,r",
						host_notification_commands="automate-policy-escalation-command",
						service_notification_period="24x7",
						service_notification_options="c,w,r",
						service_notification_commands="monitor-notify-service-by-email",
						email="not.an.email")
print command_auto.toString()
print contact_auto.toString()


command_auto = Command(command_name="automate-service-repair-command",
				 	   command_line="""/usr/share/monitor/nagios/actions/repair.py $SERVICENOTIFICATIONNUMBER$ $HOSTNOTIFICATIONNUMBER$ $NOTIFICATIONTYPE$ $HOSTNAME$ $SERVICEDESC$""")

contact_auto = Contact(contact_name="automate-service-repair-contact",
						host_notifications_enabled=1,
						service_notifications_enabled=1,
						host_notification_period="24x7",
						host_notification_options="d,r",
						host_notification_commands="monitor-notify-host-by-email",
						service_notification_period="24x7",
						service_notification_options="c,w,r",
						service_notification_commands="automate-service-repair-command",
						email="not.an.email")

print command_auto.toString()
print contact_auto.toString()

command_cluster = Command(command_name="check_service_cluster",
					 command_line="$USER1$/check_cluster --service -l $ARG1$ -w $ARG2$ -c $ARG3$ -d $ARG4$")
print command_cluster.toString()

command_cluster = Command(command_name="check_cluster",
					 command_line="$USER1$/check_cluster --host -l $ARG1$ -w $ARG2$ -c $ARG3$ -d $ARG4$")
print command_cluster.toString()


command_auto = Command(command_name="automate-host-reboot-command",
				 	   command_line="""/usr/share/monitor/nagios/actions/reboot.py $NOTIFICATIONTYPE$ $HOSTNAME$""")

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
				#('SSH806', "Auxiliary SSH Service"),
				('MODE', "PLC Node Mode"),
				('PCU', "PLC PCU status"),
				#('HTTP', "PlanetFlow HTTP"),
				#('COTOP', "HTTP based COTOP"),
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
					first_notification_delay=0, # 60*24*.5, # wait half a day before taking any action
					#contact_groups="admins",
					register="0"),
			  Service(name="planetlab-service",
					active_checks_enabled="1",
					passive_checks_enabled="1",
					parallelize_check="1",
					obsess_over_service="1",
					check_freshness="0",
					notifications_enabled="0",
					event_handler_enabled="1",
					flap_detection_enabled="1",
					failure_prediction_enabled="1",
					process_perf_data="1",
					retain_status_information="1",
					retain_nonstatus_information="1",
					is_volatile="0",
					check_period="24x7",
					max_check_attempts="3",
					normal_check_interval="30", 	# NOTE: make this reasonable for N machines.
					retry_check_interval="5",
					notification_options="w,u,c,r",
					notification_interval="60",
					notification_period="24x7",
					register="0")
			]

for obj in globalhost + globalservices:
	print obj.toString()


l_sites = plc.api.GetSites({'login_base' : ['asu', 'gmu', 'gt']})
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

ServiceDependency
hg = HostGroup(hostgroup_name="allsites", alias="allsites")
print hg.toString()

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

	#print hg.toString()


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
				host_name="%s" % hn,
				alias=hn,
				address=ip,
				d2_coords=coords,
				statusmap_image="icon-system.png",
				)
				#hostgroups=lb)

		print h.toString()

		hostname_list.append(hn)
	
	# NOTE: use all hostnames at site to create HostEscalations for down-notices
	if len(hostname_list) > 0:

		hn_list = ",".join(hostname_list)


		# NOTE: this encodes 2 OK nodes as the threshold.
		c=len(hostname_list)-1
		w=len(hostname_list)-2
		hs = ",".join([ "$HOSTSTATEID:%s$" % h for h in hostname_list ])
		ss = ",".join([ "$SERVICESTATEID:%s:aSSH$" % h for h in hostname_list ])

		dummy_site_host = Host(host_name="site-cluster-for-%s" % lb,
						use="generic-host",
						alias="site-%s" % lb,
						address="1.1.1.1",
						check_command="""check_cluster!"site-%s"!%s!%s!%s""" % (lb, w, c, hs),

						check_period="24x7",
						check_interval="120",
						retry_interval="1",
						max_check_attempts="1",
						first_notification_delay=0, # 60*24*.5, # wait half a day before taking any action

						hostgroups="allsites")

		# NOTE: without a dummy site service that checks basically the same
		# 		thing, there is nothing to display for the service-status-details
		# 		page for 'allsites'
		print dummy_site_host.toString()
		dummy_site_service = Service(use="planetlab-service",
							host_name="site-cluster-for-%s" % lb,
							service_description="LoginSSH",
							display_name="LoginSSH",
							notifications_enabled="0",
							check_command="""check_service_cluster!"site-%s"!%s!%s!%s""" % (lb, w, c, ss))
		print dummy_site_service.toString()


		# NOTE: before sending any notices, attempt to reboot host twice
		he_reboot = HostEscalation(host_name=hn_list,
						first_notification=1,
						last_notification=2,
						notification_interval=20, # 24*60*.25,
						escalation_options="d",
						contacts="automate-host-reboot-contact")
		print he_reboot.toString()

		# NOTE: as long as the site-cluster is down, run the escalation
		he_escalate = HostEscalation(host_name="site-cluster-for-%s" % lb,
						first_notification=1,
						last_notification=0,
						notification_interval=20, # 24*60*.25,
						escalation_options="d,r",
						contacts="automate-policy-escalation-contact",)
		print he_escalate.toString()

		# NOTE: always send notices to techs
		he1 = HostEscalation( host_name="site-cluster-for-%s" % lb,
						first_notification=1,
						last_notification=0,
						notification_interval=40, # 24*60*.5,
						escalation_options="r,d",
						contact_groups="%s-techs" % lb)

		# NOTE: only send notices to PIs after a week. (2 prior notices) 
		he2 = HostEscalation( host_name="site-cluster-for-%s" % lb,
						first_notification=4,
						last_notification=0,
						notification_interval=40, # 24*60*.5,
						escalation_options="r,d",
						contact_groups="%s-pis" % lb)

		# NOTE: send notices to Slice users after two weeks. (4 prior notices) 
		he3 = HostEscalation( host_name="site-cluster-for-%s" % lb,
						first_notification=7,
						last_notification=0,
						notification_interval=40, # 24*60*.5,
						escalation_options="r,d",
						contact_groups="%s-sliceusers" % lb)

		for he in [he1, he2, he3]:
			print he.toString()

		s1 = Service(use="planetlab-service",
					host_name=hn_list,
					service_description="aSSH",
					display_name="aSSH",
					servicegroups="NET,SSH",
					check_command="check_ssh!-t 120")
		s2 = Service(use="planetlab-service",
					host_name=hn_list,
					service_description="bMODE",
					display_name="bMODE",
					servicegroups="NET,MODE",
					notifications_enabled="1",
					check_command="check_mode")
		s3 = Service(use="planetlab-service",
					host_name=hn_list,
					service_description="cPCU",
					notes_url="http://www.planet-lab.org/db/sites/index.php?id=%s" % site['site_id'],
					display_name="cPCU",
					servicegroups="NET,PCU",
					notifications_enabled="1",
					check_command="check_pcu")

		# NOTE: try to repair the host, if it is online and 'mode' indicates a problem
		se1 = ServiceEscalation(host_name=hn_list,
								service_description="bMODE",
								first_notification=1,
								last_notification=0,
								escalation_options="w,c,r",
								notification_interval=20,
								contacts="automate-service-repair-contact")

		se2 = ServiceEscalation( host_name=hn_list,
								service_description="cPCU",
								first_notification=1,
								last_notification=0,
								notification_interval=40, # 24*60*.5,
								escalation_options="w,c,r",
								contact_groups="%s-techs" % lb)


		#sd1 = ServiceDependency(host_name=hn_list,
		#						service_description="aSSH",
		#						dependent_service_description="bSSH806,cHTTP,dCOTOP",
		#						execution_failure_criteria="w,u,c,p",)

		for service in [s1,s2,s3,se1,se2]:
			print service.toString()

