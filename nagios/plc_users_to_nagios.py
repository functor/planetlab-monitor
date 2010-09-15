#!/usr/bin/python

from nagiosobjects import *
import plc
from generic import *
import sys


def getContactsAndContactGroupsFor(lb, type, email_list, testing=True):

	if len(email_list) == 0:
		cg1 = ContactGroup(contactgroup_name="%s-%s" % (lb,type),
						alias="%s-%s" % (lb,type))
		return [cg1]

	contact_list = []
	person_list = []
	count = 0
	for person in email_list:
		# TODO: for testing!
		if testing:
			person="soltesz+%s%s%s@cs.princeton.edu" % ( lb, type, count )
		c1 = Contact(contact_name=person.replace("+", ""),
						host_notifications_enabled=1,
						service_notifications_enabled=1,
						host_notification_period="24x7",
						service_notification_period="24x7",
						host_notification_options="d,r,s",
						service_notification_options="c,w,r",
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


print Command(command_name="monitor-notify-host-by-email",
    						 command_line="""/usr/share/monitor/nagios/actions/mail.py --host 1 --servicenotificationnumber $SERVICENOTIFICATIONNUMBER$ --hostnotificationnumber $HOSTNOTIFICATIONNUMBER$ --notificationtype $NOTIFICATIONTYPE$ --hostname $HOSTNAME$ --hoststate $HOSTSTATE$ --hostaddress $HOSTADDRESS$ --hostoutput "$HOSTOUTPUT$" --longdatetime "$LONGDATETIME$" --notificationitype $NOTIFICATIONTYPE$ --contactemail $CONTACTEMAIL$""").toString()

print Command(command_name="monitor-notify-service-by-email",
    						    command_line="""/usr/share/monitor/nagios/actions/mail.py --service 1 --servicenotificationnumber $SERVICENOTIFICATIONNUMBER$ --hostnotificationnumber $HOSTNOTIFICATIONNUMBER$ --notificationtype $NOTIFICATIONTYPE$ --hostname $HOSTNAME$ --hoststate $HOSTSTATE$ --hostaddress $HOSTADDRESS$ --hostoutput "$HOSTOUTPUT$" --longdatetime "$LONGDATETIME$" --notificationitype $NOTIFICATIONTYPE$ --servicedesc $SERVICEDESC$ --hostalias $HOSTALIAS$ --contactemail $CONTACTEMAIL$ --servicestate "$SERVICESTATE$" --serviceoutput "$SERVICEOUTPUT$" --contactgroupname $CONTACTGROUPNAME$ """).toString()


l_sites = plc.api.GetSites({'peer_id' : None})
#l_sites = plc.api.GetSites({'login_base' : ['asu', 'gmu', 'gt']})
#l_sites = plc.api.GetSites([10243, 22, 10247, 138, 139, 10050, 10257, 
#                            18, 20, 21, 10134, 24, 10138, 10141, 30, 31, 
#                            33, 10279, 41, 29, 10193, 10064, 81, 10194, 
#                            10067, 87, 10208, 10001, 233, 157, 10100, 10107])

test_emails = False
if len(sys.argv) > 1:
    test_emails = True

for index,site in enumerate(l_sites):
	shortname = site['abbreviated_name']
	lb = site['login_base']
	print >>sys.stderr, "Collecting emails for %s (%s/%s)" % (lb, index, len(l_sites))

	# NOTE: do duplcate groups create duplicate emails?
	cl1 = getContactsAndContactGroupsFor(lb, "techs", plc.getTechEmails(lb), test_emails)
	cl2 = getContactsAndContactGroupsFor(lb, "pis", plc.getPIEmails(lb), test_emails)
	# NOTE: slice users will change often.
	cl3 = getContactsAndContactGroupsFor(lb, "sliceusers", plc.getSliceUserEmails(lb), test_emails)

	for c in [cl1,cl2,cl3]:
		for i in c:
			print i.toString()

