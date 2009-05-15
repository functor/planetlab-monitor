import turbogears as tg
from turbogears import controllers, expose, flash, exception_handler
from turbogears import widgets
from cherrypy import request, response
import cherrypy
# from monitorweb import model
# import logging
# log = logging.getLogger("monitorweb.controllers")
import re
from monitor.database.info.model import *
#from monitor.database.zabbixapi.model import *
#from monitor.database.dborm import zab_session as session
#from monitor.database.dborm import zab_metadata as metadata
from monitor_xmlrpc import MonitorXmlrpcServer

from monitor import reboot
from monitor import scanapi

from monitor.wrapper.plccache import plcdb_id2lb as site_id2lb
from monitor.wrapper.plccache import plcdb_hn2lb as site_hn2lb
from monitor.wrapper.plccache import plcdb_lb2hn as site_lb2hn

from monitorweb.templates.links import *



def query_to_dict(query):
	""" take a url query string and chop it up """
	val = {}
	query_fields = query.split('&')
	for f in query_fields:
		(k,v) = urllib.splitvalue(f)
		val[k] = v

	return val

def format_ports(data, pcumodel=None):
	retval = []
	filtered_length=0

	if pcumodel:
		supported_ports=reboot.model_to_object(pcumodel).supported_ports
	else:
		# ports of a production node
		supported_ports=[22,80,806]

	if data and len(data.keys()) > 0 :
		for port in supported_ports:
			try:
				state = data[str(port)]
			except:
				state = "unknown"

			if state == "filtered":
				filtered_length += 1
				
			retval.append( (port, state) )

	if retval == []: 
		retval = [( "Closed/Filtered", "state" )]

	if filtered_length == len(supported_ports):
		retval = [( "All Filtered", "state" )]

	return retval

def format_pcu_shortstatus(pcu):
	status = "error"
	if pcu:
		if pcu.reboot_trial_status == str(0):
			status = "Ok"
		elif pcu.reboot_trial_status == "NetDown" or pcu.reboot_trial_status == "Not_Run":
			status = pcu.reboot_trial_status
		else:
			status = "error"

	return status

def prep_pcu_for_display(pcu):
		
	try:
		pcu.loginbase = site_id2lb[pcu.plc_pcu_stats['site_id']]
	except:
		pcu.loginbase = "unknown"

	pcu.ports = format_ports(pcu.port_status, pcu.plc_pcu_stats['model'])
	pcu.status = format_pcu_shortstatus(pcu)

	#print pcu.entry_complete
	pcu.entry_complete_str = pcu.entry_complete
	#pcu.entry_complete_str += "".join([ f[0] for f in pcu.entry_complete.split() ])
	if pcu.dns_status == "NOHOSTNAME":
		pcu.dns_short_status = 'NoHost'
	elif pcu.dns_status == "DNS-OK":
		pcu.dns_short_status = 'Ok'
	elif pcu.dns_status == "DNS-NOENTRY":
		pcu.dns_short_status = 'NoEntry'
	elif pcu.dns_status == "NO-DNS-OR-IP":
		pcu.dns_short_status = 'NoHostOrIP'
	elif pcu.dns_status == "DNS-MISMATCH":
		pcu.dns_short_status = 'Mismatch'

class NodeWidget(widgets.Widget):
	pass

def prep_node_for_display(node):
	if node.plc_pcuid:
		pcu = FindbadPCURecord.get_latest_by(plc_pcuid=node.plc_pcuid)
		if pcu:
			node.pcu_status = pcu.reboot_trial_status
			node.pcu_short_status = format_pcu_shortstatus(pcu)
			node.pcu = pcu
			prep_pcu_for_display(node.pcu)
		else:
			node.pcu_short_status = "none"
			node.pcu_status = "nodata"
			node.pcu = None

	else:
		node.pcu_status = "nopcu"
		node.pcu_short_status = "none"
		node.pcu = None


	if node.kernel_version:
		node.kernel = node.kernel_version.split()[2]
	else:
		node.kernel = ""

	try:
		node.loginbase = site_id2lb[node.plc_node_stats['site_id']]
	except:
		node.loginbase = "unknown"

	if node.loginbase:
		node.site = HistorySiteRecord.by_loginbase(node.loginbase)
		if node.site is None:
			# TODO: need a cleaner fix for this...
			node.site = HistorySiteRecord.by_loginbase("pl")
                        if not node.site:
                                node.site = HistorySiteRecord.by_loginbase("ple")
			

	node.history = HistoryNodeRecord.by_hostname(node.hostname)

	node.ports = format_ports(node.port_status)

	try:
		exists = node.plc_node_stats['last_contact']
	except:
		node.plc_node_stats = {'last_contact' : None}



class Root(controllers.RootController, MonitorXmlrpcServer):
	@expose(template="monitorweb.templates.welcome")
	def index(self):
		import time
		# log.debug("Happy TurboGears Controller Responding For Duty")
		flash("Your application is now running")
		return dict(now=time.ctime())

	@expose(template="monitorweb.templates.pcuview")
	def nodeview(self, hostname=None):
		nodequery=[]
		if hostname:
                        node = FindbadNodeRecord.get_latest_by(hostname=hostname)
                        # NOTE: reformat some fields.
                        prep_node_for_display(node)
                        nodequery += [node]

		return self.pcuview(None, None, hostname) # dict(nodequery=nodequery)

	@expose(template="monitorweb.templates.nodelist")
	def node(self, filter='boot'):
		import time
		fbquery = FindbadNodeRecord.get_all_latest()
		query = []
		filtercount = {'down' : 0, 'boot': 0, 'debug' : 0, 'diagnose' : 0, 'disabled': 0, 
						'neverboot' : 0, 'pending' : 0, 'all' : 0, None : 0}
		for node in fbquery:
			# NOTE: reformat some fields.
			prep_node_for_display(node)

			#node.history.status
			print node.hostname

			if node.history.status in ['down', 'offline']:
				if node.plc_node_stats and node.plc_node_stats['last_contact'] != None:
					filtercount['down'] += 1
				else:
					filtercount['neverboot'] += 1
			elif node.history.status in ['good', 'online']:
				filtercount['boot'] += 1
			elif node.history.status in ['debug', 'monitordebug']:
				filtercount['debug'] += 1
			else:
                                # TODO: need a better fix. filtercount
                                # doesn't maps to GetBootStates() on
                                # 4.3 so this one fails quite often.
                                if filtercount.has_key(node.history.status):
                                        filtercount[node.history.status] += 1
				
			## NOTE: count filters
			#if node.observed_status != 'DOWN':
			#	print node.hostname, node.observed_status
			#	if node.observed_status == 'DEBUG':
			#		if node.plc_node_stats['boot_state'] in ['debug', 'diagnose', 'disabled']:
			#			filtercount[node.plc_node_stats['boot_state']] += 1
			#		else:
			#			filtercount['debug'] += 1
			#			
			#	else:
			#		filtercount[node.observed_status] += 1
			#else:
			#	if node.plc_node_stats and node.plc_node_stats['last_contact'] != None:
			#		filtercount[node.observed_status] += 1
			#	else:
			#		filtercount['neverboot'] += 1

			# NOTE: apply filter
			if filter == "neverboot":
				if not node.plc_node_stats or node.plc_node_stats['last_contact'] == None:
					query.append(node)
			elif filter == "all":
				query.append(node)
			elif filter == node.history.status:
				query.append(node)
			elif filter == 'boot':
				query.append(node)

			#if filter == node.observed_status:
			#	if filter == "DOWN":
			#		if node.plc_node_stats['last_contact'] != None:
			#			query.append(node)
			#	else:
			#		query.append(node)
			#elif filter == "neverboot":
			#	if not node.plc_node_stats or node.plc_node_stats['last_contact'] == None:
			#		query.append(node)
			#elif filter == "pending":
			#	# TODO: look in message logs...
			#	pass
			#elif filter == node.plc_node_stats['boot_state']:
			#	query.append(node)
			#elif filter == "all":
			#	query.append(node)
				
		widget = NodeWidget(template='monitorweb.templates.node_template')
		return dict(now=time.ctime(), query=query, fc=filtercount, nodewidget=widget)
	
	def nodeaction_handler(self, tg_exceptions=None):
		"""Handle any kind of error."""
		print "NODEACTION_HANDLER------------------"

		if 'pcuid' in request.params:
			pcuid = request.params['pcuid']
		else:
			refurl = request.headers.get("Referer",link("pcu"))
			print refurl

			# TODO: do this more intelligently...
			uri_fields = urllib.splitquery(refurl)
			if uri_fields[1] is not None:
				val = query_to_dict(uri_fields[1])
				if 'pcuid' in val:
					pcuid = val['pcuid']
				elif 'hostname' in val:
					pcuid = FindbadNodeRecord.get_latest_by(hostname=val['hostname']).plc_pcuid
				else:
					pcuid=None
			else:
				pcuid=None

		cherry_trail = cherrypy._cputil.get_object_trail()
		for i in cherry_trail:
			print "trail: ", i

		print pcuid
		return self.pcuview(None, pcuid, **dict(exceptions=tg_exceptions))

	def nodeaction(self, **data):
		print "NODEACTION------------------"
		for item in data.keys():
			print "%s %s" % ( item, data[item] )

		if 'hostname' in data:
			hostname = data['hostname']
		else:
			flash("No hostname given in submitted data")
			return

		if 'submit' in data or 'type' in data:
			try:
				action = data['submit']
			except:
				action = data['type']
		else:
			flash("No submit action given in submitted data")
			return

		if action == "Reboot":
			print "REBOOT: %s" % hostname
			ret = reboot.reboot_str(str(hostname))
			print ret
			if ret: raise RuntimeError("Error using PCU: " + str(ret))
			flash("Reboot appeared to work.  Allow at most 5 minutes.  Then run ExternalScan to check current status.")

		elif action == "ExternalScan":
			scanapi.externalprobe(str(hostname))
			flash("External Scan Successful!")
		elif action == "InternalScan":
			scanapi.internalprobe(str(hostname))
			flash("Internal Scan Successful!")
		else:
			# unknown action
			raise RuntimeError("Unknown action given")
		return

	# TODO: add form validation
	@expose(template="monitorweb.templates.pcuview")
	@exception_handler(nodeaction_handler,"isinstance(tg_exceptions,RuntimeError)")
	def pcuview(self, loginbase=None, pcuid=None, hostname=None, **data):
		print "PCUVIEW------------------"
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		sitequery=[]
		pcuquery=[]
		nodequery=[]
		actions=[]
		exceptions = None

		for key in data:
			print key, data[key]

		if 'submit' in data.keys() or 'type' in data.keys():
			if hostname: data['hostname'] = hostname
			self.nodeaction(**data)
		if 'exceptions' in data:
			exceptions = data['exceptions']

		if loginbase:
			actions = ActionRecord.query.filter_by(loginbase=loginbase
							).filter(ActionRecord.date_created >= datetime.now() - timedelta(14)
							).order_by(ActionRecord.date_created.desc())
			actions = [ a for a in actions ]
			sitequery = [HistorySiteRecord.by_loginbase(loginbase)]
			pcus = {}
			for plcnode in site_lb2hn[loginbase]:
					node = FindbadNodeRecord.get_latest_by(hostname=plcnode['hostname'])
					# NOTE: reformat some fields.
					prep_node_for_display(node)
					nodequery += [node]
					if node.plc_pcuid: 	# not None
						pcu = FindbadPCURecord.get_latest_by(plc_pcuid=node.plc_pcuid)
						prep_pcu_for_display(pcu)
						pcus[node.plc_pcuid] = pcu

			for pcuid_key in pcus:
				pcuquery += [pcus[pcuid_key]]

		if pcuid and hostname is None:
			print "pcuid: %s" % pcuid
			pcu = FindbadPCURecord.get_latest_by(plc_pcuid=pcuid)
			# NOTE: count filter
			prep_pcu_for_display(pcu)
			pcuquery += [pcu]
			if 'site_id' in pcu.plc_pcu_stats:
				sitequery = [HistorySiteRecord.by_loginbase(pcu.loginbase)]
				
			if 'nodenames' in pcu.plc_pcu_stats:
				for nodename in pcu.plc_pcu_stats['nodenames']: 
					print "query for %s" % nodename
					node = FindbadNodeRecord.get_latest_by(hostname=nodename)
					print "%s" % node.port_status
					print "%s" % node.to_dict()
					if node:
						prep_node_for_display(node)
						nodequery += [node]

		if hostname and pcuid is None:
				node = FindbadNodeRecord.get_latest_by(hostname=hostname)
				# NOTE: reformat some fields.
				prep_node_for_display(node)
				sitequery = [node.site]
				nodequery += [node]
				if node.plc_pcuid: 	# not None
					pcu = FindbadPCURecord.get_latest_by(plc_pcuid=node.plc_pcuid)
					prep_pcu_for_display(pcu)
					pcuquery += [pcu]
			
		return dict(sitequery=sitequery, pcuquery=pcuquery, nodequery=nodequery, actions=actions, exceptions=exceptions)

	@expose(template="monitorweb.templates.nodehistory")
	def nodehistory(self, hostname=None):
		query = []
		if hostname:
			#fbnode = FindbadNodeRecord.get_by(hostname=hostname)
			## TODO: add links for earlier history if desired.
			#l = fbnode.versions[-100:]
			#l.reverse()
			#for node in l:
			#	prep_node_for_display(node)
			#	query.append(node)

			fbnode = HistoryNodeRecord.get_by(hostname=hostname)
			l = fbnode.versions[-100:]
			l.reverse()
			for node in l:
				#prep_node_for_display(node)
				query.append(node)

		return dict(query=query, hostname=hostname)

	@expose(template="monitorweb.templates.sitehistory")
	def sitehistory(self, loginbase=None):
		query = []
		if loginbase:
			fbsite = HistorySiteRecord.get_by(loginbase=loginbase)
			# TODO: add links for earlier history if desired.
			l = fbsite.versions[-100:]
			l.reverse()
			for site in l:
				query.append(site)
		return dict(query=query, loginbase=loginbase)


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

			prep_pcu_for_display(node)

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

	@expose(template="monitorweb.templates.siteview")
	def siteview(self, loginbase='pl'):
		# get site query
		sitequery = [HistorySiteRecord.by_loginbase(loginbase)]
		nodequery = []
		for plcnode in site_lb2hn[loginbase]:
			for node in FindbadNodeRecord.get_latest_by(hostname=plcnode['hostname']):
				# NOTE: reformat some fields.
				prep_node_for_display(node)
				nodequery += [node]
		return dict(sitequery=sitequery, nodequery=nodequery, fc={})

	@expose(template="monitorweb.templates.sitelist")
	def site(self, filter='all'):
		filtercount = {'good' : 0, 'down': 0, 'online':0, 'offline' : 0, 'new' : 0, 'pending' : 0, 'all' : 0}
		fbquery = HistorySiteRecord.query.all()
		query = []
		for site in fbquery:
			# count filter
			filtercount['all'] += 1
			if site.new and site.slices_used == 0 and not site.enabled:
				filtercount['new'] += 1
			elif not site.enabled:
				filtercount['pending'] += 1
			elif site.status in ['good', 'online']:
				filtercount['good'] += 1
			elif site.status in ['down', 'offline']:
				filtercount['down'] += 1

			# apply filter
			if filter == "all":
				query.append(site)
			elif filter == 'new' and site.new and site.slices_used == 0 and not site.enabled:
				query.append(site)
			elif filter == "pending" and not site.enabled:
				query.append(site)
			elif filter == 'good' and site.status in ['good', 'online']:
				query.append(site)
			elif filter == 'down' and site.status in ['down', 'offline']:
				query.append(site)
				
		return dict(query=query, fc=filtercount)

	@expose(template="monitorweb.templates.actionlist")
	def action(self, filter='all'):
		session.bind = metadata.bind
		filtercount = {'active' : 0, 'acknowledged': 0, 'all' : 0}
		# With Acknowledgement
		sql_ack = 'SELECT DISTINCT h.host,t.description,t.priority,t.lastchange,a.message,e.eventid '+ \
              ' FROM triggers t,hosts h,items i,functions f, hosts_groups hg,escalations e,acknowledges a ' + \
              ' WHERE f.itemid=i.itemid ' + \
                  ' AND h.hostid=i.hostid ' + \
                  ' AND hg.hostid=h.hostid ' + \
                  ' AND t.triggerid=f.triggerid ' + \
                  ' AND t.triggerid=e.triggerid ' + \
                  ' AND a.eventid=e.eventid ' + \
                  ' AND t.status=' + str(defines.TRIGGER_STATUS_ENABLED) + \
                  ' AND i.status=' + str(defines.ITEM_STATUS_ACTIVE) + \
                  ' AND h.status=' + str(defines.HOST_STATUS_MONITORED) + \
                  ' AND t.value=' + str(defines.TRIGGER_VALUE_TRUE) + \
              ' ORDER BY t.lastchange DESC';

		# WithOUT Acknowledgement
		sql_noack = 'SELECT DISTINCT h.host,t.description,t.priority,t.lastchange,e.eventid ' + \
              ' FROM triggers t,hosts h,items i,functions f, hosts_groups hg,escalations e,acknowledges a ' + \
              ' WHERE f.itemid=i.itemid ' + \
                  ' AND h.hostid=i.hostid ' + \
                  ' AND hg.hostid=h.hostid ' + \
                  ' AND t.triggerid=f.triggerid ' + \
                  ' AND t.triggerid=e.triggerid ' + \
                  ' AND e.eventid not in (select eventid from acknowledges) ' + \
                  ' AND t.status=' + str(defines.TRIGGER_STATUS_ENABLED) + \
                  ' AND i.status=' + str(defines.ITEM_STATUS_ACTIVE) + \
                  ' AND h.status=' + str(defines.HOST_STATUS_MONITORED) + \
                  ' AND t.value=' + str(defines.TRIGGER_VALUE_TRUE) + \
              ' ORDER BY t.lastchange DESC';
		# for i in session.execute(sql): print i

		query=[]
		replace = re.compile(' {.*}')
		for sql,ack in [(sql_ack,True), (sql_noack,False)]:
			result = session.execute(sql)
			for row in result:
				try:
					newrow = [ site_hn2lb[row[0].lower()] ] + [ r for r in row ]
				except:
					print site_hn2lb.keys()
					newrow = [ "unknown" ] + [ r for r in row ]

				newrow[2] = replace.sub("", newrow[2]) # strip {.*} expressions

				# NOTE: filter count
				filtercount['all'] += 1
				if not ack: # for unacknowledged
					filtercount['active'] += 1
					if filter == 'active':
						query.append(newrow)
				else:
					filtercount['acknowledged'] += 1
					if filter == 'acknowledged':
						query.append(newrow)
					
				if filter != "acknowledged" and filter != "active":
					query.append(newrow)

		return dict(query=query, fc=filtercount)
