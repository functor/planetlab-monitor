import turbogears as tg
from turbogears import controllers, expose, flash
# from monitorweb import model
# import logging
# log = logging.getLogger("monitorweb.controllers")
from monitor.database.info.model import *
from pcucontrol import reboot

def format_ports(pcu):
	retval = []
	if pcu.port_status and len(pcu.port_status.keys()) > 0 :
		obj = reboot.model_to_object(pcu.plc_pcu_stats['model'])
		for port in obj.supported_ports:
			state = pcu.port_status[str(port)]
			retval.append( (port, state) )

	if retval == []: 
		retval = [( "Closed/Filtered", "state" )]

	return retval

def format_pcu_shortstatus(pcu):
	status = "error"
	if pcu.reboot_trial_status == str(0):
		status = "ok"
	elif pcu.reboot_trial_status == "NetDown" or pcu.reboot_trial_status == "Not_Run":
		status = pcu.reboot_trial_status
	else:
		status = "error"

	return status

class Root(controllers.RootController):
	@expose(template="monitorweb.templates.welcome")
	def index(self):
		import time
		# log.debug("Happy TurboGears Controller Responding For Duty")
		flash("Your application is now running")
		return dict(now=time.ctime())

	@expose(template="monitorweb.templates.nodelist")
	def node(self, filter='BOOT'):
		import time
		fbquery = FindbadNodeRecord.get_all_latest()
		query = []
		filtercount = {'DOWN' : 0, 'BOOT': 0, 'DEBUG' : 0, 'neverboot' : 0, 'pending' : 0, 'all' : 0}
		for node in fbquery:
			if node.plc_pcuid:
				pcu = FindbadPCURecord.get_latest_by(plc_pcuid=node.plc_pcuid).first()
				if pcu:
					node.pcu_status = pcu.reboot_trial_status
				else:
					node.pcu_status = "nodata"
			else:
				node.pcu_status = "nopcu"

			if node.kernel_version:
				node.kernel = node.kernel_version.split()[2]
			else:
				node.kernel = ""

			# NOTE: count filters
			if node.observed_status != 'DOWN':
				filtercount[node.observed_status] += 1
			else:
				if node.plc_node_stats['last_contact'] != None:
					filtercount[node.observed_status] += 1
				else:
					filtercount['neverboot'] += 1

			# NOTE: apply filter
			if filter == node.observed_status:
				if filter == "DOWN":
					if node.plc_node_stats['last_contact'] != None:
						query.append(node)
				else:
					query.append(node)
			elif filter == "neverboot":
				if node.plc_node_stats['last_contact'] == None:
					query.append(node)
			elif filter == "pending":
				# TODO: look in message logs...
				pass
			elif filter == "all":
				query.append(node)
				
		return dict(now=time.ctime(), query=query, fc=filtercount)

	@expose(template="monitorweb.templates.pculist")
	def pcu(self, filter='all'):
		import time
		fbquery = FindbadPCURecord.get_all_latest()
		query = []
		filtercount = {'ok' : 0, 'NetDown': 0, 'Not_Run' : 0, 'pending' : 0, 'all' : 0}
		for node in fbquery:

			# NOTE: count filter
			if node.reboot_trial_status == str(0):
				filtercount['ok'] += 1
			elif node.reboot_trial_status == 'NetDown' or node.reboot_trial_status == 'Not_Run':
				filtercount[node.reboot_trial_status] += 1
			else:
				filtercount['pending'] += 1
				
			print reboot.pcu_name(node.plc_pcu_stats)
			node.ports = format_ports(node)
			node.status = format_pcu_shortstatus(node)

			# NOTE: apply filter
			if filter == "all":
				query.append(node)
			elif filter == "ok" and node.reboot_trial_status == str(0):
				query.append(node)
			elif filter == node.reboot_trial_status:
				query.append(node)
			elif filter == "pending":
				# TODO: look in message logs...
				if node.reboot_trial_status != str(0) and \
					node.reboot_trial_status != 'NetDown' and \
					node.reboot_trial_status != 'Not_Run':

					query.append(node)
				
		return dict(query=query, fc=filtercount)

	@expose(template="monitorweb.templates.pculist")
	def site(self, filter='all'):
		filtercount = {'ok' : 0, 'NetDown': 0, 'Not_Run' : 0, 'pending' : 0, 'all' : 0}
		return dict(query=[], fc=filtercount)

	@expose(template="monitorweb.templates.pculist")
	def action(self, filter='all'):
		filtercount = {'ok' : 0, 'NetDown': 0, 'Not_Run' : 0, 'pending' : 0, 'all' : 0}
		return dict(query=[], fc=filtercount)
