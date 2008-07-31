#!/usr/bin/python

import soltesz
import plc

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

class Service(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "service", **kwargs)

class ServiceDependency(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicedependency", **kwargs)

class ServiceGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicegroup", **kwargs)


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
					check_interval="60",
					retry_interval="5",
					max_check_attempts="10",
					check_command="check-host-alive",
					contact_groups="admins",
					register="0")]

for obj in globalhost + globalservices:
	print obj.toString()

plcdb = soltesz.dbLoad("l_plcsites")
netid2ip = soltesz.dbLoad("plcdb_netid2ip")
lb2hn = soltesz.dbLoad("plcdb_lb2hn")

for site in plcdb:
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
		nodes = lb2hn[site['login_base']] # plc.getSiteNodes2(site['login_base'])
	else:
		continue

	if len(nodes) == 0:
		continue

	print hg.toString()

	for node in nodes:
		hn = node['hostname']
		if len(node['nodenetwork_ids']) == 0:
			continue

		ip = netid2ip[node['nodenetwork_ids'][0]]

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

		for service in [s1,s2,s3,s4,sd1,sd2,sd3]:
			print service.toString()

