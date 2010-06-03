#!/usr/bin/python

class NagiosObject(object):
	trans = {'d2_coords': '2d_coords'}

	def __init__(self, id, **kwargs):
		self.id = id
		self.kwords = kwargs.keys()
		for key in self.kwords:
			self.__setattr__(key, kwargs[key])

	def toString(self):
		ret = ""
		ret += "define %s {\n" % self.id
		for key in self.kwords:
			if key in self.trans:
				ret += "    %s   %s\n" % (self.trans[key], self.__getattribute__(key))
			else:
				ret += "    %s   %s\n" % (key, self.__getattribute__(key))
		ret += "}\n"
		return ret

class Host(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "host", **kwargs)

class HostGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "hostgroup", **kwargs)

class HostEscalation(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "hostescalation", **kwargs)

class Contact(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "contact", **kwargs)

class ContactGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "contactgroup", **kwargs)

class Service(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "service", **kwargs)

class ServiceDependency(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicedependency", **kwargs)

class ServiceEscalation(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "serviceescalation", **kwargs)

class ServiceGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicegroup", **kwargs)

def getContactsAndContactGroupsFor(lb, type, email_list):

	contact_list = []
	for person in email_list:
		c1 = Contact(contact_name=person,
						host_notifications_enabled=1,
						service_notifications_enabled=1,
						host_notification_period="24x7",
						service_notification_period="24x7",
						host_notification_options="d,r,s",
						service_notification_options="c,r",
						host_notification_commands="notify-by-email",
						service_notification_commands="notify-by-email",
						email=person)
		contact_list.append(c1)

	cg1 = ContactGroup(contactgroup_name="%s-%s" % (lb,type),
						alias="%s-%s" % (lb,type),
						members=",".join(email_list))

	contact_list.append(cg1)

	return contact_list


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


globalhost = [Host(	name="planetlab-host",
					use="generic-host",
					check_period="24x7",
					check_interval="120",
					retry_interval="10",
					max_check_attempts="6",
					check_command="check-host-alive",
					contact_groups="admins",
					register="0")]

for obj in globalhost + globalservices:
	print obj.toString()

from monitor.wrapper import plccache

plcdb = plccache.l_sites
netid2ip = plccache.d_from_l(plccache.plc.api.GetInterfaces(), 'interface_id')
lb2hn = plccache.plcdb_lb2hn

sites = plccache.plc.api.GetSites([10243, 22, 10247, 138, 139, 10050, 10257, 18, 20, 
							21, 10134, 24, 10138, 10141, 30, 31, 33, 10279, 41, 29, 10193, 10064, 81,
							10194, 10067, 87, 10208, 10001, 233, 157, 10100, 10107])

for site in sites:
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

	# NOTE: do duplcate groups create duplicate emails?
	cl1 = getContactsAndContactGroupsFor(lb, "techs", plccache.plc.getTechEmails(lb))
	cl2 = getContactsAndContactGroupsFor(lb, "pis", plccache.plc.getPIEmails(lb))
	# NOTE: slice users will change often.
	cl3 = getContactsAndContactGroupsFor(lb, "sliceusers", plccache.plc.getSliceUserEmails(lb))

	for c in [cl1,cl2,cl3]:
		for i in c:
			print i.toString()

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

		s1 = Service(use="generic-service",
					host_name=hn,
					service_description="aSSH",
					display_name="aSSH",
					servicegroups="NET,SSH",
					check_command="check_ssh!-t 120")
		s2 = Service(use="generic-service",
					host_name=hn,
					service_description="bSSH806",
					display_name="bSSH806",
					servicegroups="NET,SSH806",
					check_command="check_ssh!-p 806 -t 120")
		s3 = Service(use="generic-service",
					host_name=hn,
					service_description="cHTTP",
					display_name="cHTTP",
					servicegroups="NET,HTTP",
					check_command="check_http!-t 120")
		s4 = Service(use="generic-service",
					host_name=hn,
					service_description="dCOTOP",
					display_name="dCOTOP",
					servicegroups="NET,COTOP",
					check_command="check_http!-p 3120 -t 120")

		se1 = ServiceEscalation( host_name=hn,
						service_description='aSSH',
						first_notification=0,
						last_notification=2,
						notification_interval=24*60*3.5,
						escalation_options="r,c",
						contact_groups="%s-techs" % lb)

		se2 = ServiceEscalation( host_name=hn,
						service_description='aSSH',
						first_notification=2,
						last_notification=4,
						notification_interval=24*60*3.5,
						escalation_options="r,c",
						contact_groups="%s-techs,%s-pis" % (lb,lb))

		se3 = ServiceEscalation( host_name=hn,
						service_description='aSSH',
						first_notification=4,
						last_notification=0,
						notification_interval=24*60*3.5,
						escalation_options="r,c",
						contact_groups="%s-techs,%s-pis,%s-sliceusers" % (lb,lb,lb))

		sd1 = ServiceDependency(host_name=hn,
								service_description="aSSH",
								dependent_host_name=hn,
								dependent_service_description="bSSH806",
								execution_failure_criteria="w,u,c,p",)

		sd2 = ServiceDependency(host_name=hn,
								service_description="aSSH",
								dependent_host_name=hn,
								dependent_service_description="cHTTP",
								execution_failure_criteria="w,u,c,p",)

		sd3 = ServiceDependency(host_name=hn,
								service_description="aSSH",
								dependent_host_name=hn,
								dependent_service_description="dCOTOP",
								execution_failure_criteria="w,u,c,p",)

		for service in [s1,s2,s3,s4,se1,se2,se3,sd1,sd2,sd3]:
			print service.toString()

