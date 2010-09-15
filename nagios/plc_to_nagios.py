#!/usr/bin/python

import plc
from plc_config import *
from nagiosobjects import *
from generic import *
import auth
import socket

print Command(command_name="check_plc_api",
              command_line="""/usr/share/monitor/nagios/plugins/checkplc.py -H $HOSTNAME$ """).toString()

#print Command(command_name="check_plc_web",
#              command_line="""/usr/share/monitor/nagios/plugins/checkplc.py -H $HOSTNAME$ --sn $SERVICENOTIFICATIONNUMBER$ """).toString()

#print Command(command_name="check_plc_db",
#              command_line="""/usr/share/monitor/nagios/plugins/checkplc.py -H $HOSTNAME$ --sn $SERVICENOTIFICATIONNUMBER$ """).toString()


globalhost = [Host(    name="planetlab-server",
                    use="generic-host",
                    check_period="24x7",
                    check_interval="120",
                    retry_interval="10",
                    max_check_attempts="6",
                    check_command="check_http",
                    first_notification_delay=0, # 60*24*.5, # wait half a day before taking any action
                    contact_groups="admins",
                    register="0"),

              Service(name="planetlab-server-service",
                    active_checks_enabled="1",
                    passive_checks_enabled="1",
                    parallelize_check="1",
                    obsess_over_service="1",
                    check_freshness="0",
                    notifications_enabled="1",
                    event_handler_enabled="1",
                    flap_detection_enabled="1",
                    failure_prediction_enabled="1",
                    process_perf_data="1",
                    retain_status_information="1",
                    retain_nonstatus_information="1",
                    is_volatile="0",
                    check_period="24x7",
                    max_check_attempts="3",
                    normal_check_interval="15",     # NOTE: make this reasonable for N machines.
                    retry_check_interval="5",
                    notification_options="w,u,c,r",
                    notification_interval="60",
                    notification_period="24x7",
                    contact_groups="admins",
                    register="0")
            ]

globalservices = []
for service in [('HTTP', "HTTP Server"),
                ('API', "PLC API"),
                ]:
    globalservices.append(ServiceGroup(servicegroup_name=service[0], alias=service[1]))

for obj in globalhost + globalservices:
    print obj.toString()

#plc_hosts = [ PLC_MONITOR_HOST, PLC_WWW_HOST, PLC_BOOT_HOST, PLC_PLANETFLOW_HOST, ]
plc_hosts = [ PLC_WWW_HOST, PLC_BOOT_HOST, ]

print HostGroup(hostgroup_name="allplcservers", alias="allplcservers").toString()

hostname_list = []
for host in plc_hosts:
    shortname = host
    ip = socket.gethostbyname(host)
            
    h = Host(use="planetlab-server",
                host_name="%s" % host,
                alias=host,
                address=ip,
                hostgroups="allplcservers")

    print h.toString()

    hostname_list.append(host)
    
# NOTE: use all hostnames at site to create HostEscalations for down-notices
if len(hostname_list) > 0:

    hn_list = ",".join(hostname_list)

    s1 = Service(use="planetlab-server-service",
                    host_name=hn_list,
                    service_description="API",
                    display_name="API",
                    servicegroups="NET,API",
                    check_command="check_plc_api")

        ## NOTE: try to repair the host, if it is online and 'mode' indicates a problem
        #se1 = ServiceEscalation(host_name=hn_list,
        #                        service_description="bRUNLEVEL",
        #                        first_notification=1,
        #                        last_notification=0,
        #                        escalation_options="w,c,r",
        #                        notification_interval=20,
        #                        contacts="automate-service-repair-contact")

    for service in [s1]:
        print service.toString()

