#!/usr/bin/python

from nagiosobjects import *

def getContactsAndContactGroupsFor(lb, type, email_list):

	if len(email_list) == 0:
		cg1 = ContactGroup(contactgroup_name="%s-%s" % (lb,type),
						alias="%s-%s" % (lb,type))
						
		return [cg1]

	contact_list = []
	person_list = []
	count = 0
	for person in email_list:
		# TODO: for testing!
		person="soltesz+%s%s%s@cs.princeton.edu" % ( lb, type, count )
		c1 = Contact(contact_name=person.replace("+", ""),
						host_notifications_enabled=1,
						service_notifications_enabled=1,
						host_notification_period="24x7",
						service_notification_period="24x7",
						host_notification_options="d,r,s",
						service_notification_options="c,r",
						host_notification_commands="monitor-notify-host-by-email",
						service_notification_commands="monitor-notify-service-by-email",
						email=person)
		count += 1
		contact_list.append(c1)
		person_list.append(person.replace("+",""))

	cg1 = ContactGroup(contactgroup_name="%s-%s" % (lb,type),
						alias="%s-%s" % (lb,type),
						members=",".join(person_list))

	contact_list.append(cg1)

	return contact_list


host_email_command = Command(command_name="monitor-notify-host-by-email",
    						 command_line="""/usr/share/monitor/nagios/actions/mail.py --servicenotificationnumber $SERVICENOTIFICATIONNUMBER$ --hostnotificationnumber $HOSTNOTIFICATIONNUMBER$ --notificationtype $NOTIFICATIONTYPE$ --hostname $HOSTNAME$ --hoststate $HOSTSTATE$ --hostaddress $HOSTADDRESS$ --hostoutput "$HOSTOUTPUT$" --longdatetime "$LONGDATETIME$" --notificationitype $NOTIFICATIONTYPE$ --contactemail $CONTACTEMAIL$""")

service_email_command = Command(command_name="monitor-notify-service-by-email",
    							command_line="""/usr/bin/printf "%b" "***** MyOpsNagios $SERVICENOTIFICATIONNUMBER$ $HOSTNOTIFICATIONNUMBER$ *****\\n\\nNotification Type: $NOTIFICATIONTYPE$\\n\\nService: $SERVICEDESC$\\nHost: $HOSTALIAS$\\nAddress: $HOSTADDRESS$\\nState: $SERVICESTATE$\\n\\nDate/Time: $LONGDATETIME$\\n\\nAdditional Info:\\n\\n$SERVICEOUTPUT$" | /bin/mail -S replyto=monitor@planet-lab.org -s "** $NOTIFICATIONTYPE$ Service Alert: $HOSTALIAS$/$SERVICEDESC$ is $SERVICESTATE$ **" $CONTACTEMAIL$""")


print host_email_command.toString()
print service_email_command.toString()


import plc
from generic import *


l_sites = plc.api.GetSites({'login_base' : ['asu', 'gmu', 'gt']})
#l_sites = plc.api.GetSites([10243, 22, 10247, 138, 139, 10050, 10257, 18, 20, 
#							21, 10134, 24, 10138, 10141, 30, 31, 33, 10279, 41, 29, 10193, 10064, 81,
#							10194, 10067, 87, 10208, 10001, 233, 157, 10100, 10107])


for site in l_sites:
	shortname = site['abbreviated_name']
	lb = site['login_base']

	# NOTE: do duplcate groups create duplicate emails?
	cl1 = getContactsAndContactGroupsFor(lb, "techs", plc.getTechEmails(lb))
	cl2 = getContactsAndContactGroupsFor(lb, "pis", plc.getPIEmails(lb))
	# NOTE: slice users will change often.
	cl3 = getContactsAndContactGroupsFor(lb, "sliceusers", plc.getSliceUserEmails(lb))

	for c in [cl1,cl2,cl3]:
		for i in c:
			print i.toString()

