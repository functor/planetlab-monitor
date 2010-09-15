#!/usr/bin/python

import plc
from nagiosobjects import *
from generic import *
import auth
import sys


t_interval = int(sys.argv[1])
i_nodecount = int(sys.argv[2])
testing = int(sys.argv[3])



print Command(command_name="check_mode",
                        command_line="""/usr/share/monitor/nagios/plugins/checkmode.py -H $HOSTNAME$ --sn $SERVICENOTIFICATIONNUMBER$ """).toString()

print Command(command_name="check_pcu",
                        command_line="""/usr/share/monitor/nagios/plugins/checkpcu.py -H $HOSTNAME$ """).toString()

if not testing:
    print Command(command_name="check_rt",
                  command_line="""/usr/share/monitor/nagios/plugins/checkrt.py -p $ARG1$ -p $ARG2$ """).toString()
else:
    print Command(command_name="check_rt",
                  command_line="""/usr/share/monitor/nagios/fake_rt.sh -p $ARG1$ """).toString()

print Command(command_name="check_escalation",
                 command_line="""/usr/share/monitor/nagios/plugins/checkescalation.py --site $ARG1$ """).toString()

print Command(command_name="check_cycle",
        command_line="""/usr/share/monitor/nagios/plugins/checkcycle.py --type $ARG1$ -H $HOSTNAME$ """).toString()

print Command(command_name="check_fake",
        command_line="""/usr/share/monitor/nagios/status.sh $HOSTNAME$ """).toString()

print Command(command_name="check_service_cluster",
                     command_line="$USER1$/check_cluster --service -l $ARG1$ -w $ARG2$ -c $ARG3$ -d $ARG4$").toString()

print Command(command_name="check_cluster",
                     command_line="$USER1$/check_cluster --host -l $ARG1$ -w $ARG2$ -c $ARG3$ -d $ARG4$").toString()

print Command(command_name="check_dummy",
              command_line="$USER1$/check_dummy $ARG1$ \"$ARG2$\"").toString()

command_auto = Command(command_name="automate-policy-escalation-command",
                        command_line="""/usr/share/monitor/nagios/actions/escalation.py --site $HOSTNAME$ --notificationnumber $SERVICENOTIFICATIONNUMBER$ --notificationtype $NOTIFICATIONTYPE$ $SERVICEDURATIONSEC$ """)
contact_auto = Contact(contact_name="automate-policy-escalation-contact",
                        host_notifications_enabled=0,
                        service_notifications_enabled=1,
                        host_notification_period="24x7",
                        host_notification_options="d,r",
                        host_notification_commands="notify-service-by-email",
                        service_notification_period="24x7",
                        service_notification_options="c,w,r",
                        service_notification_commands="automate-policy-escalation-command",
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
                        host_notification_commands="notify-host-by-email",
                        service_notification_period="24x7",
                        service_notification_options="c,w,r",
                        service_notification_commands="automate-service-repair-command",
                        email="not.an.email")

print command_auto.toString()
print contact_auto.toString()


command_auto = Command(command_name="automate-host-reboot-command",
                        command_line="""/usr/share/monitor/nagios/actions/reboot.py $NOTIFICATIONTYPE$ $HOSTNAME$""")

contact_auto = Contact(contact_name="automate-host-reboot-contact",
                        host_notifications_enabled=1,
                        host_notification_period="24x7",
                        host_notification_options="d,r",
                        host_notification_commands="automate-host-reboot-command",
                        service_notifications_enabled=1,
                        service_notification_period="24x7",
                        service_notification_options="c,w,r",
                        service_notification_commands="automate-host-reboot-command",
                        email="not.an.email")

print command_auto.toString()
print contact_auto.toString()

globalservices = []
for service in [('NET', "Network Services"),
                ('SSH', "SSH Service"),
                ('TICKET', "RT Ticket Status"),
                ('RUNLEVEL', "Node Runlevel"),
                ('PCU', "PCU status"),
                ]:
    globalservices.append(ServiceGroup(servicegroup_name=service[0], alias=service[1]))


service_check_interval=t_interval
host_check_interval=2*service_check_interval
retry_interval = int(service_check_interval/5)
action_notification_interval=2*service_check_interval
email_notification_interval=4*service_check_interval


# NOTE: since ping is not a reliable check in the wide area, use 'check_ssh'
#         to determine if the host is minimally online.  If we cannot access
#         port 22 it, then it is DOWN.

globalhost = [Host(    name="planetlab-host",
                    use="generic-host",
                    check_period="24x7",
                    check_interval=host_check_interval,
                    retry_interval=retry_interval,
                    max_check_attempts="6",
                    #check_command="check_fake",
                    #check_command="check_ssh!-t 120",
                    check_command="check_dummy!0!Stub check for host services",
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
                    normal_check_interval=service_check_interval, # NOTE: make this reasonable for N machines.
                    retry_check_interval=retry_interval,
                    notification_options="w,u,c,r",
                    notification_interval=action_notification_interval,
                    notification_period="24x7",
                    #contact_groups="admins",
                    register="0")
            ]

for obj in globalhost + globalservices:
    print obj.toString()


#l_sites = plc.api.GetSites({'peer_id' : None})
#l_sites = plc.api.GetSites({'login_base' : ['asu', 'utah', 'uncc']})
#l_sites = plc.api.GetSites({'login_base' : ['asu', 'gmu', 'gt']})
l_sites = plc.api.GetSites([10243, 22, 10247, 138, 139, 10050, 10257, 
                            18, 20, 21, 10134, 24, 10138, 10141, 30, 31, 
                            33, 10279, 41, 29, 10193, 10064, 81, 10194, 
                            10067, 87, 10208, 10001, 233, 157, 10100, 10107])

#for site in l_sites:
#    lb = site['login_base']
#    print "./blacklist.py --site %s --add --expires $(( 60*60*24*30 ))" % lb
#sys.exit(1)


node_ids = [ s['node_ids'] for s in l_sites ]
node_ids = [ map(str,n) for n in node_ids ] 
node_ids = filter(lambda x: len(x) > 0, node_ids)
node_ids = [ ",".join(n) for n in node_ids ] 
node_ids = ",".join(node_ids)
node_ids = map(int, node_ids.split(","))

l_nodes = plc.api.GetNodes(node_ids)

(d_sites,id2lb) = dsites_from_lsites_id(l_sites)
(plcdb, hn2lb, lb2hn) = dsn_from_dsln(d_sites, id2lb, l_nodes)

netid2ip = d_from_l(plc.api.GetInterfaces(), 'interface_id')

print HostGroup(hostgroup_name="allsites", alias="allsites").toString()
print HostGroup(hostgroup_name="allplchosts", alias="allplchosts").toString()

host_count = 0

for site in l_sites:
    if testing and host_count >= i_nodecount:
        break   # stop after we've output at least i_nodecount nodes.
    shortname = site['abbreviated_name']
    lb = site['login_base']
    site_hostgroup = "site-cluster-for-%s" % lb
    hg = HostGroup(hostgroup_name=site_hostgroup, alias=shortname)
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
            
        print Host(use="planetlab-host",
                host_name="%s" % hn,
                alias=hn,
                address=ip,
                d2_coords=coords,
                statusmap_image="icon-system.png",
                hostgroups="allplchosts,%s" % site_hostgroup).toString()

        hostname_list.append(hn)
        host_count += 1
    
    # NOTE: use all hostnames at site to create HostEscalations for down-notices
    if len(hostname_list) > 0:

        hn_list = ",".join(hostname_list)

        # NOTE: this encodes 2 OK nodes as the threshold.
        c=len(hostname_list)-1
        if len(hostname_list) > 1:
            w=len(hostname_list)-2
        else:
            w=c
        hs = ",".join([ "$HOSTSTATEID:%s$" % h for h in hostname_list ])
        ss = ",".join([ "$SERVICESTATEID:%s:aSSH$" % h for h in hostname_list ])

        print Host(host_name="site-cluster-for-%s" % lb,
                        use="generic-host",
                        alias="site-cluster-for-%s" % lb,
                        address="1.1.1.1",
                        # NOTE: *10 is to guarantee the site is always ok.
                        #check_command="""check_cluster!"site-cluster-for-%s"!%s!%s!%s""" % (lb, w*10, c*10, hs),
                        check_command="""check_dummy!0!Stub site for %s""" %lb, 
                        check_period="24x7",
                        check_interval=host_check_interval,
                        retry_interval=retry_interval,
                        max_check_attempts="1",
                        first_notification_delay=0, # 60*24*.5, # wait half a day before taking any action
                        hostgroups="allsites,%s" % site_hostgroup).toString()

        # NOTE: without a dummy site service that checks basically the same
        #         thing, there is nothing to display for the service-status-details
        #         page for 'allsites'
        print Service(use="planetlab-service",
                            host_name="site-cluster-for-%s" % lb,
                            service_description="SiteOnline",
                            display_name="SiteOnline",
                            notifications_enabled="1",
                            check_command="""check_service_cluster!"site-cluster-for-%s"!%s!%s!%s""" % (lb, w, c, ss)).toString()
        print Service(use="planetlab-service",
                            host_name="site-cluster-for-%s" % lb,
                            service_description="RtTickets",
                            display_name="RtTickets",
                            servicegroups="NET,TICKET",
                            notifications_enabled="0",
                            check_command="""check_rt!"site-cluster-for-%s"!%s%%aSSH """ % (lb,lb)).toString()

		#print Service(use="planetlab-service",
		#					host_name="site-cluster-for-%s" % lb,
		#					service_description="PolicyLevel",
		#					display_name="PolicyLevel",
		#					notifications_enabled="0",
		#					check_command="""check_escalation!"site-cluster-for-%s" """ % lb).toString()

        # NOTE: always send notices to techs
        print ServiceEscalation( host_name="site-cluster-for-%s" % lb,
                        service_description="SiteOnline",
                        first_notification=1,
                        last_notification=0,
                        notification_interval=email_notification_interval,
                        escalation_options="c,w,r",
                        contact_groups="%s-techs" % lb).toString()

        # NOTE: as long as the site-cluster is down, run the escalation
        print ServiceEscalation(host_name="site-cluster-for-%s" % lb,
                        service_description="SiteOnline",
                        first_notification=1,
                        last_notification=0,
                        notification_interval=action_notification_interval,
                        escalation_options="c,w,r",
                        contacts="automate-policy-escalation-contact",).toString()

        # NOTE: only send SiteOnline failure notices when RtTickets are OK.
        #       if someone replies to a notice, then RtTickets will be not-OK,
        #       and suspend SiteOnline notices.
        print ServiceDependency(
                        host_name="site-cluster-for-%s" % lb,
                        service_description="RtTickets",
                        dependent_host_name="site-cluster-for-%s" % lb,
                        dependent_service_description="SiteOnline",
                        execution_failure_criteria='n',
                        notification_failure_criteria="c,w").toString()


        ##########################################################################
        ##########################################################################
        ##########################################################################

        # NOTE: Check that we're not stuck in a loop.
        print Service(use="planetlab-service",
                    host_name=hn_list,
                    service_description="0-CycleCheck",
                    notifications_enabled="1",
                    display_name="0-CycleCheck",
                    check_command="check_cycle!rebootlog").toString()
        # NOTE: If we are in a loop, then let someone know.
        print ServiceEscalation(host_name=hn_list,
                        service_description="0-CycleCheck",
                        first_notification=1,
                        last_notification=0,
                        notification_interval=email_notification_interval,
                        escalation_options="c,w",
                        contact_groups="admins").toString()
        # NOTE: Stop other Escalations if the CycleCheck fails.
        print ServiceDependency(
                        host_name=hn_list,
                        service_description="0-CycleCheck",
                        dependent_host_name=hn_list,
                        dependent_service_description="aSSH",
                        execution_failure_criteria='c,w',
                        notification_failure_criteria="c,w").toString()
        print ServiceDependency(
                        host_name=hn_list,
                        service_description="0-CycleCheck",
                        dependent_host_name=hn_list,
                        dependent_service_description="bRUNLEVEL",
                        execution_failure_criteria='c,w',
                        notification_failure_criteria="c,w").toString()

        # NOTE: define services that run on the host.
        print Service(use="planetlab-service",
                    host_name=hn_list,
                    service_description="aSSH",
                    notifications_enabled="1",
                    display_name="aSSH",
                    servicegroups="NET,SSH",
                    check_command="check_ssh!-t 120").toString()
        # NOTE: before sending any notices, attempt to reboot host twice
        print ServiceEscalation(host_name=hn_list,
                        service_description="aSSH",
                        first_notification=1,
                        last_notification=2,
                        notification_interval=action_notification_interval,
                        escalation_options="c",
                        contacts="automate-host-reboot-contact").toString()
        # NOTE: after trying to reboot the node, send periodic notices regarding this host being down. 
        #       Even if the site is not down, some notice should go out.
        print ServiceEscalation( host_name=hn_list,
                        service_description="aSSH",
                        first_notification=3,
                        last_notification=0,
                        notification_interval=email_notification_interval*2,
                        escalation_options="c,w,r",
                        contact_groups="%s-techs" % lb).toString()

        #print Service(use="planetlab-service",
        #            host_name=hn_list,
        #            service_description="cPCU",
        #            notes_url="%s/db/sites/index.php?id=%s" % (auth.www, site['site_id']),
        #            display_name="cPCU",
        #            servicegroups="NET,PCU",
        #            notifications_enabled="0",
        #            check_command="check_pcu").toString()
        #print ServiceDependency(
        #                host_name="boot.planet-lab.org",
        #                service_description="API",
        #                dependent_host_name=hn_list,
        #                dependent_service_description="cPCU",
        #                execution_failure_criteria='c,w',
        #                notification_failure_criteria="c,w").toString()
        #print ServiceEscalation( host_name=hn_list,
        #                service_description="cPCU",
        #                first_notification=1,
        #                last_notification=0,
        #                notification_interval=40, # 24*60*.5,
        #                escalation_options="w,c,r",
        #                contact_groups="%s-techs" % lb).toString()

        print Service(use="planetlab-service",
                    host_name=hn_list,
                    service_description="bRUNLEVEL",
                    display_name="bRUNLEVEL",
                    servicegroups="NET,RUNLEVEL",
                    notifications_enabled="1",
                    check_command="check_mode").toString()
        # NOTE: check runlevel cannot run without the API
        print ServiceDependency(
                        host_name="boot.planet-lab.org",
                        service_description="API",
                        dependent_host_name=hn_list,
                        dependent_service_description="bRUNLEVEL",
                        execution_failure_criteria='c,w',
                        notification_failure_criteria="c,w").toString()
        # NOTE: check_mode critical is probably offline. warning is repairable.
        # NOTE: try to repair the host, if it is online and 'mode' indicates a problem
        print ServiceEscalation(host_name=hn_list,
                    service_description="bRUNLEVEL",
                    first_notification=1,
                    last_notification=0,
                    escalation_options="w",
                    notification_interval=action_notification_interval,
                    contacts="automate-service-repair-contact").toString()
