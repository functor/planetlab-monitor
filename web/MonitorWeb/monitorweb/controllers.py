import turbogears as tg
from turbogears import controllers, expose, flash, exception_handler, redirect
from turbogears import widgets
from cherrypy import request, response
import cherrypy
# from monitorweb import model
# import logging
# log = logging.getLogger("monitorweb.controllers")
import re
import os
from monitor.database.info.model import *
#from monitor.database.zabbixapi.model import *
from monitor_xmlrpc import MonitorXmlrpcServer

from monitor import util
from monitor import reboot
from monitor import bootman
from monitor import scanapi
from monitor import config
import time

from monitor.wrapper.plccache import plcdb_hn2lb as site_hn2lb

from monitorweb.templates.links import *

class ObjectQueryFields(widgets.WidgetsList):
	"""The WidgetsList defines the fields of the form."""
	pass



class NodeQueryFields(widgets.WidgetsList):
	"""The WidgetsList defines the fields of the form."""

	object = widgets.RadioButtonList(label="Query Type", options=[('nodes', 'All Nodes'), 
															  ('nodehistory', 'Single Node History'),
															  #('sites', 'All Sites'),
															  #('sitehistory', 'Single Site History'),
															  ], default="nodes")
	nodehistory_hostname = widgets.TextField(label="Hostname Node History", attrs={'size':30})

	hostname = widgets.CheckBox(label="Hostname")
	firewall = widgets.CheckBox(label="Firewall?")
	fs_status = widgets.CheckBox(label="Filesystem Status")
	ssh_status = widgets.CheckBox(label="SSH Status")
	ssh_error = widgets.CheckBox(label="SSH Errors")
	dns_status = widgets.CheckBox(label="DNS Status")
	iptables_status = widgets.CheckBox(label="IP Tables Status")
	nm_status = widgets.CheckBox(label="NM Status")
	princeton_comon_dir = widgets.CheckBox(label="CoMon Dir")
	princeton_comon_running = widgets.CheckBox(label="CoMon Running")
	princeton_comon_procs = widgets.CheckBox(label="CoMon Processes")
	external_dns_status = widgets.CheckBox(label="Hostname Resolves?")
	kernel_version = widgets.CheckBox(label="Kernel")
	bootcd_version = widgets.CheckBox(label="BootCD")
        boot_server = widgets.CheckBox(label="Boot Server")
        install_date = widgets.CheckBox(label="Installation Date")
	observed_status = widgets.CheckBox(label="Observed Status")
	uptime = widgets.CheckBox(label="Uptime")
	traceroute = widgets.CheckBox(label="Traceroute")
	port_status = widgets.CheckBox(label="Port Status")
	rpms = widgets.CheckBox(label="RPM")
	rpmvalue = widgets.TextField(label="RPM Pattern")

class QueryForm(widgets.TableForm):
    template = """
    <form xmlns:py="http://purl.org/kid/ns#"
        id="queryform"
        name="${name}"
        action="${action}"
        method="${method}"
        class="tableform"
        py:attrs="form_attrs"
    >
        <div py:for="field in hidden_fields"
            py:replace="field.display(value_for(field), **params_for(field))"
        />
        <table border="0" cellspacing="0" cellpadding="2" py:attrs="table_attrs">
            <tr py:for="i, field in enumerate(fields)"
                class="${i%2 and 'odd' or 'even'}"
            >
                <th>
                    <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
                </th>
                <td>
                    <span py:replace="field.display(value_for(field), **params_for(field))" />
                    <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                    <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
                </td>
            </tr>
            <tr>
                <td>&#160;</td>
                <td py:content="submit.display(submit_text)" />
            </tr>
        </table>
    </form>
	"""

def getNodeQueryForm():
	return QueryForm(fields=NodeQueryFields(), action="query")

# make it easier group objects without invoking the elixir auto-write feature.
class aggregate: pass


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
	agg = aggregate()
	agg.pcu = pcu 
		
	try:
		agg.loginbase = PlcSite.query.get(pcu.plc_pcu_stats['site_id']).plc_site_stats['login_base']
	except:
		agg.loginbase = "unknown"

	agg.pcuhist = HistoryPCURecord.query.get(pcu.plc_pcuid)

	agg.ports = format_ports(pcu.port_status, pcu.plc_pcu_stats['model'])
	agg.status = format_pcu_shortstatus(pcu)

	#print pcu.entry_complete
	agg.entry_complete_str = pcu.entry_complete
	#pcu.entry_complete_str += "".join([ f[0] for f in pcu.entry_complete.split() ])
	if pcu.dns_status == "NOHOSTNAME":
		agg.dns_short_status = 'NoHost'
	elif pcu.dns_status == "DNS-OK":
		agg.dns_short_status = 'Ok'
	elif pcu.dns_status == "DNS-NOENTRY":
		agg.dns_short_status = 'NoEntry'
	elif pcu.dns_status == "NO-DNS-OR-IP":
		agg.dns_short_status = 'NoHostOrIP'
	elif pcu.dns_status == "DNS-MISMATCH":
		agg.dns_short_status = 'Mismatch'
	return agg

class ActionListWidget(widgets.Widget):
	pass

class NodeWidget(widgets.Widget):
	pass

def prep_nodehist(node):
	agg = aggregate()
	agg.node = node
	agg.loginbase = "unknown"
	try:
		agg.loginbase = PlcSite.query.get(node.plc_siteid).plc_site_stats['login_base']
	except:
		agg.loginbase = "exception"
		

	return agg

def prep_node_for_display(node, pcuhash=None, preppcu=True, asofdate=None):
	agg = aggregate()
	agg.node = node

	if node.plc_pcuid and preppcu:
		if pcuhash:
			pcu = pcuhash[node.plc_pcuid]
		else:
			pcu = FindbadPCURecord.get_latest_by(plc_pcuid=node.plc_pcuid)

		if pcu:
			agg.pcu_status = pcu.reboot_trial_status
			agg.pcu_short_status = format_pcu_shortstatus(pcu)
			agg.pcu = prep_pcu_for_display(pcu)
		else:
			agg.pcu_short_status = "none"
			agg.pcu_status = "nodata"
			agg.pcu = None

	else:
		agg.pcu_status = "nopcu"
		agg.pcu_short_status = "none"
		agg.pcu = None


	if node.kernel_version:
		agg.kernel = node.kernel_version.split()[2]
	else:
		agg.kernel = ""

	try:
		agg.loginbase = PlcSite.query.get(node.plc_node_stats['site_id']).plc_site_stats['login_base']
	except:
		agg.loginbase = "unknown"

	if agg.loginbase:
		agg.site = HistorySiteRecord.by_loginbase(agg.loginbase)

		if asofdate:
			agg.site = agg.site.get_as_of(asofdate)

		if agg.site is None:
			# TODO: need a cleaner fix for this...
			agg.site = HistorySiteRecord.by_loginbase("pl")
			if not agg.site:
				agg.site = HistorySiteRecord.by_loginbase("ple")

	agg.history = HistoryNodeRecord.by_hostname(node.hostname)
	if asofdate:
		agg.history = agg.history.get_as_of(asofdate)

	agg.ports = format_ports(node.port_status)

	try:
		exists = node.plc_node_stats['last_contact']
	except:
		# TODO: this should not assign to the fb object!
		node.plc_node_stats = {'last_contact' : None}
	
	return agg


class Root(controllers.RootController, MonitorXmlrpcServer):
	@expose(template="monitorweb.templates.welcome")
	def index(self):
		# log.debug("Happy TurboGears Controller Responding For Duty")
		flash("Welcome To MyOps!")
		return dict(now=time.ctime())

	@expose(template="monitorweb.templates.nodelist", allow_json=True)
	def node3(self, filter=None):
		nhquery = HistoryNodeRecord.query.all()
		query = []
		for nh in nhquery:
			if filter:
				if nh.status == filter:
					query.append(nh)
			else:
				query.append(nh)

		rquery=[]
		for q in query:
			fb = FindbadNodeRecord.get_latest_by(hostname=q.hostname)
			rquery.append(fb)

		return dict(now=time.ctime(), query=rquery)

	def node_query(self, filter):
		nhquery = HistoryNodeRecord.query.all()
		query = []
		for nh in nhquery:
			if filter:
				if nh.status == filter:
					query.append(nh)
			else:
				query.append(nh)

		rquery=[]
		for q in query:
			fb = FindbadNodeRecord.get_latest_by(hostname=q.hostname)
			agg = prep_node_for_display(fb)
			rquery.append(agg)
		return rquery

	@expose("cheetah:monitorweb.templates.nodelist_plain", as_format="plain", 
		accept_format="text/plain", content_type="text/plain")
	@expose(template="monitorweb.templates.nodelist", allow_json=True)
	def node2(self, filter=None):
		rquery=self.node_query(filter)
		widget = NodeWidget(template='monitorweb.templates.node_template')
		return dict(now=time.ctime(), query=rquery, nodewidget=widget)

	@expose("cheetah:monitorweb.templates.query_plain", as_format="plain", 
		accept_format="text/plain", content_type="text/plain")
	@expose(template="monitorweb.templates.query", allow_json=True)
	def query(self, **data):
		query = []

		for k in data:
			print k, data[k]

		fbquery = None
		
		if 'object' in data and data['object'] == "nodes":
			fbquery = FindbadNodeRecord.get_all_latest()
		elif 'object' in data and data['object'] == "nodehistory": 
			hostname = data['nodehistory_hostname']
			data['date_checked'] = 'date_checked'
			fbrecord = FindbadNodeRecord.get_by(hostname=hostname)
			fbquery = fbrecord.versions[-500:]

		if fbquery:
			for node in fbquery:
				# NOTE: reformat some fields.
				if type(node) is not type(FindbadNodeRecord):
					agg = node.__dict__.copy()
				else:
					agg = node.to_dict()
				agg.update(agg['plc_node_stats'])
				if agg['kernel_version']:
					agg['kernel_version'] = agg['kernel_version'].split()[2]
				if 'traceroute' in data and agg['traceroute']:
					agg['traceroute'] = "<pre>" + agg['traceroute'] + "</pre>"
				if 'rpmvalue' in data and 'rpms' in data:
					if agg['rpms']:
						rpm_list = agg['rpms'].split()
						rpm_list = filter(lambda x: data['rpmvalue'] in x, rpm_list)
						agg['rpms'] = " ".join(rpm_list)

				query.append(agg)

		fields=data.copy()

		try: 
			del fields['object']
			del fields['rpmvalue']
			del fields['nodehistory_hostname']
		except: pass
		return dict(now=time.ctime(), query=query, fields=fields, data=data, queryform=getNodeQueryForm())

	@expose(template="monitorweb.templates.nodefast", allow_json=True)
	def node(self, filter=None):
		nhquery = HistoryNodeRecord.query.all()
		query = []
		for nh in nhquery:
			if filter:
				if nh.status == filter:
					agg = prep_nodehist(nh)
					query.append(agg)
			else:
				agg = prep_nodehist(nh)
				query.append(agg)

		return dict(now=time.ctime(), query=query)

	@expose(template="monitorweb.templates.nodelist")
	def nodeslow(self, filter='boot'):
		print "NODE------------------"
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
		fbquery = FindbadNodeRecord.get_all_latest()
		query = []
		filtercount = {'down' : 0, 'boot': 0, 'debug' : 0, 'diagnose' : 0, 'disabled': 0, 
						'neverboot' : 0, 'pending' : 0, 'all' : 0, None : 0}
		for node in fbquery:
			# NOTE: reformat some fields.
			agg = prep_node_for_display(node)

			if not agg.history:
				continue

			if agg.history.status in ['down', 'offline']:
				if node.plc_node_stats and node.plc_node_stats['last_contact'] != None:
					filtercount['down'] += 1
				else:
					filtercount['neverboot'] += 1
			elif agg.history.status in ['good', 'online']:
				filtercount['boot'] += 1
			elif agg.history.status in ['debug', 'monitordebug']:
				filtercount['debug'] += 1
			else:
				if filtercount.has_key(agg.history.status):
					filtercount[agg.history.status] += 1
				

			# NOTE: apply filter
			if filter == "neverboot":
				if not node.plc_node_stats or node.plc_node_stats['last_contact'] == None:
					query.append(agg)
			elif filter == "all":
				query.append(agg)
			elif filter == agg.history.status:
				query.append(agg)
			elif filter == 'boot':
				query.append(agg)

				
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

	@expose(template="monitorweb.templates.simpleview")
	def simpleview(self, **data):
		return self.pre_view(**data)

	@expose(template="monitorweb.templates.simpleview")
	def pcuview(self, **data):
		return self.pre_view(**data)

	@expose(template="monitorweb.templates.detailview")
	def detailview(self, **data):
		return self.pre_view(**data)


	def pre_view(self, **data):
		session.flush(); session.clear()

		loginbase=None
		loginbase_list=[]
		hostname=None
		pcuid=None
		since=20
		# if objtype is not None, then treat 'hostname' or 'loginbase' as a search pattern
		objtype=None

		exceptions = None
		sitequery=[]
		nodequery=[]
		pcuquery=[]
		actions=[]
		actions_list=[]

		for key in data:
			print key, data[key]

		if 'query' in data:
			obj = data['query']
			fields = obj.split(":")
			if len(fields) > 1:
				objtype = fields[0]
				obj = fields[1].replace("*", "%")
				print "obj: %s"% obj

			if len(obj.split(".")) > 1 or objtype == "node": 
				hostname = obj
			else: 
				loginbase = obj

		if 'loginbase' in data:
			loginbase = data['loginbase']

		if 'hostname' in data:
			hostname = data['hostname']

		if 'pcuid' in data:
			try: pcuid = int(data['pcuid'])
			except: pcuid = None

		if 'since' in data:
			try: since = int(since)
			except: since = 20

		if pcuid:
			print "pcuid: %s" % pcuid
			pcu = FindbadPCURecord.get_latest_by(plc_pcuid=pcuid)
			loginbase_list += [ PlcSite.query.get(pcu.plc_pcu_stats['site_id']).plc_site_stats['login_base'] ]

		if hostname:
			if not objtype:
				nodes = [ FindbadNodeRecord.get_latest_by(hostname=hostname) ]
			else:
				nodes = FindbadNodeRecord.query.filter(FindbadNodeRecord.hostname.like(hostname)) 

			for node in nodes:
				lb = PlcSite.query.get(node.plc_node_stats['site_id']).plc_site_stats['login_base']
				if lb not in loginbase_list:
					loginbase_list += [ lb ]

		if loginbase:
			if not objtype:
				loginbase_list = [ loginbase ]
			else:
				loginbase_list = HistorySiteRecord.query.filter(HistorySiteRecord.loginbase.like(loginbase)) 
				loginbase_list = [ l.loginbase for l in loginbase_list ]
			

		if loginbase_list:
			for loginbase in loginbase_list:
				actions = ActionRecord.query.filter_by(loginbase=loginbase
								).filter(ActionRecord.date_created >= datetime.now() - timedelta(since)
								).order_by(ActionRecord.date_created.desc())
				actions_list += [ a for a in actions ]
				site = HistorySiteRecord.by_loginbase(loginbase)
				if site:
					sitequery.append(site)
				# NOTE: because a single pcu may be assigned to multiple hosts,
				# track unique pcus by their plc_pcuid, then turn dict into list
				pcus = {}
				for node in FindbadNodeRecord.query.filter_by(loginbase=loginbase):
						# NOTE: reformat some fields.
						agg = prep_node_for_display(node)
						nodequery += [agg]
						if agg.pcu: 
							pcus[agg.pcu.pcu.plc_pcuid] = agg.pcu

				for pcuid_key in pcus:
					pcuquery += [pcus[pcuid_key]]

		actionlist_widget = ActionListWidget(template='monitorweb.templates.actionlist_template')
		return dict(sitequery=sitequery, pcuquery=pcuquery, nodequery=nodequery, actions=actions_list, actionlist_widget=actionlist_widget, since=since, exceptions=exceptions)


	# TODO: add form validation
	@expose(template="monitorweb.templates.pcuview")
	@exception_handler(nodeaction_handler,"isinstance(tg_exceptions,RuntimeError)")
	def pcuviewold(self, loginbase=None, pcuid=None, hostname=None, since=20, **data):
		session.flush(); session.clear()
		sitequery=[]
		pcuquery=[]
		nodequery=[]
		actions=[]
		exceptions = None

		try: since = int(since)
		except: since = 7

		for key in data:
			print key, data[key]

		if 'submit' in data.keys() or 'type' in data.keys():
			if hostname: data['hostname'] = hostname
			self.nodeaction(**data)
		if 'exceptions' in data:
			exceptions = data['exceptions']

		if 'query' in data:
			obj = data['query']
			if len(obj.split(".")) > 1: hostname = obj
			else: loginbase=obj

		if pcuid:
			print "pcuid: %s" % pcuid
			pcu = FindbadPCURecord.get_latest_by(plc_pcuid=pcuid)
			loginbase = PlcSite.query.get(pcu.plc_pcu_stats['site_id']).plc_site_stats['login_base']

		if hostname:
			node = FindbadNodeRecord.get_latest_by(hostname=hostname)
			loginbase = PlcSite.query.get(node.plc_node_stats['site_id']).plc_site_stats['login_base']

		if loginbase:
			actions = ActionRecord.query.filter_by(loginbase=loginbase
							).filter(ActionRecord.date_created >= datetime.now() - timedelta(since)
							).order_by(ActionRecord.date_created.desc())
			actions = [ a for a in actions ]
			sitequery = [HistorySiteRecord.by_loginbase(loginbase)]
			pcus = {}
			for node in FindbadNodeRecord.query.filter_by(loginbase=loginbase):
					# NOTE: reformat some fields.
					agg = prep_node_for_display(node)
					nodequery += [agg]
					if agg.pcu: #.pcu.plc_pcuid: 	# not None
						#pcu = FindbadPCURecord.get_latest_by(plc_pcuid=agg.plc_pcuid)
						#prep_pcu_for_display(pcu)
						pcus[agg.pcu.pcu.plc_pcuid] = agg.pcu

			for pcuid_key in pcus:
				pcuquery += [pcus[pcuid_key]]

		return dict(sitequery=sitequery, pcuquery=pcuquery, nodequery=nodequery, actions=actions, since=since, exceptions=exceptions)

	@expose(template="monitorweb.templates.pcuhistory")
	def pcuhistory(self, pcu_id=None):
		query = []
		if pcu_id:
			fbnode = HistoryPCURecord.get_by(plc_pcuid=pcu_id)
			l = fbnode.versions[-100:]
			l.reverse()
			for pcu in l:
				#prep_node_for_display(node)
				query.append(pcu)

		return dict(query=query, pcu_id=pcu_id)

	@expose(template="monitorweb.templates.nodescanhistory")
	def nodescanhistory(self, hostname=None, length=10):
		try: length = int(length)
		except: length = 21

		fbnode = FindbadNodeRecord.get_by(hostname=hostname)
		# TODO: add links for earlier history if desired.
		l = fbnode.versions[-length:]
		l.reverse()
		query=[]
		for node in l:
			agg = prep_node_for_display(node, pcuhash=None, preppcu=False, asofdate=node.timestamp)
			query.append(agg)

		if 'length' in request.params: 
			del request.params['length']
		return dict(query=query, hostname=hostname, params=request.params)

	@expose(template="monitorweb.templates.nodehistory")
	def nodehistory(self, hostname=None):
		query = []
		if hostname:
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
		print "PCUVIEW------------------"
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
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

			pcuagg = prep_pcu_for_display(node)

			# NOTE: apply filter
			if filter == "all":
				query.append(pcuagg)
			elif filter == "ok" and node.reboot_trial_status == str(0):
				query.append(pcuagg)
			elif filter == node.reboot_trial_status:
				query.append(pcuagg)
			elif filter == "pending":
				# TODO: look in message logs...
				if node.reboot_trial_status != str(0) and \
					node.reboot_trial_status != 'NetDown' and \
					node.reboot_trial_status != 'Not_Run':

					query.append(pcuagg)
				
		return dict(query=query, fc=filtercount)

	@expose(template="monitorweb.templates.sitelist")
	def site(self, filter='all'):
		print "SITE------------------"
		print "befor-len: ", len( [ i for i in session] )
		session.flush(); session.clear()
		print "after-len: ", len( [ i for i in session] )
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
	@expose(template="monitorweb.templates.sitesummary")
	def sitesummary(self, loginbase="princeton"):
		nodequery = []
		for node in FindbadNodeRecord.query.filter_by(loginbase=loginbase):
			agg = prep_node_for_display(node)
			nodequery += [agg]
		
		return dict(nodequery=nodequery, loginbase=loginbase)

	@expose(template="monitorweb.templates.summary")
	def summary(self, since=7):
		sumdata = {}
		sumdata['nodes'] = {}
		sumdata['sites'] = {}
		sumdata['pcus'] = {}

		def summarize(query, type):
			for o in query:
				if o.status not in sumdata[type]:
					sumdata[type][o.status] = 0
				sumdata[type][o.status] += 1

		fbquery = HistorySiteRecord.query.all()
		summarize(fbquery, 'sites')
		fbquery = HistoryPCURecord.query.all()
		summarize(fbquery, 'pcus')
		fbquery = HistoryNodeRecord.query.all()
		summarize(fbquery, 'nodes')

		if 'monitordebug' in sumdata['nodes']:
			d = sumdata['nodes']['monitordebug']
			del sumdata['nodes']['monitordebug']
			sumdata['nodes']['failboot'] = d
		
		return dict(sumdata=sumdata, setorder=['good', 'offline', 'down', 'online']) 

	@expose(template="monitorweb.templates.actionsummary")
	def actionsummary(self, since=7):
		from monitor.wrapper.emailTxt import mailtxt

		types = filter(lambda x: 'notice' in x, dir(mailtxt))
		results = {}

		print mon_metadata.bind
		if session.bind is None:
			#TODO: figure out why this value gets cleared out...
			session.bind = mon_metadata.bind
		result = session.execute("select distinct(action_type) from actionrecord;")

		types = [r[0] for r in result]

		try: since = int(since)
		except: since = 7

		for  t in types:
			acts = ActionRecord.query.filter(ActionRecord.action_type==t
					).filter(ActionRecord.date_created >= datetime.now() - timedelta(since))
			results[t] = acts.count()
		return dict(results=results)

	@expose(template="monitorweb.templates.actionlist")
	def actionlist(self, since=7, action_type=None, loginbase=None):

		try: since = int(since)
		except: since = 7

		acts_query = ActionRecord.query.filter(
					  ActionRecord.date_created >= datetime.now() - timedelta(since)
					 )
		if loginbase:
			acts_query = acts_query.filter_by(loginbase=loginbase)

		if action_type:
			acts_query = acts_query.filter(ActionRecord.action_type==action_type)

		acts = acts_query.order_by(ActionRecord.date_created.desc())

		query = [ a for a in acts ]
		
		return dict(actions=query, action_type=action_type, since=since)

	@cherrypy.expose()
	def upload(self, log, **keywords):
		hostname = None
		logtype = None
		logtype_list = ['bm.log', ]

		if 'hostname' in keywords:
			hostname = keywords['hostname']
		if 'type' in keywords and keywords['type'] in logtype_list:
			logtype = keywords['type']

		if not hostname: return ""
		if not logtype: return "unknown logtype: %s" % logtype 

		short_target_filename = bootman.bootmanager_log_name(hostname)
		abs_target_filename = os.path.join(config.MONITOR_BOOTMANAGER_LOG, short_target_filename)
		print "write data: %s" % abs_target_filename
		util.file.dumpFile(abs_target_filename, log.file.read())
		bootman.bootmanager_log_action(hostname, short_target_filename, logtype)
		session.flush()

		print "redirecting 3"

		return dict()
