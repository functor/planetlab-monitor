#!/usr/bin/python

from os import getcwd
from os.path import dirname, exists, join
import sys
import md5

from monitor import config
from monitor.database.dborm import * 
from monitor.database.zabbixapi.emailZabbix import *
from monitor.database.zabbixapi import defines



HOSTGROUP_NAME="%s_hostgroup"
USERGROUP_NAME="%s_usergroup"
	
DISCOVERY_RULE_NAME="discovery rule for %s"
DISCOVERY_ACTION_NAME="Auto-discover %s action"
ESCALATION_ACTION_NAME="Escalation Action for %s"

def delete_site(loginbase):

	# get host group, usrgrp
	# get all users in usrgrp, delete each
	usergroupname = USERGROUP_NAME % loginbase
	hostgroupname = HOSTGROUP_NAME % loginbase
	discovery_action_name = DISCOVERY_ACTION_NAME % loginbase
	discovery_rule_name = DISCOVERY_RULE_NAME % loginbase
	escalation_action_name = ESCALATION_ACTION_NAME % loginbase

	ug = UsrGrp.get_by(name=usergroupname)
	if ug:
		for user in ug.user_list:
			# remove user from group, if a member of no other groups, 
			# delete user.
			#user.delete()
			pass
		ug.delete()

	hg = HostGroup.get_by(name=hostgroupname)
	if hg: 
		# figure out how to delete all the hosts...
		# NOTE: hosts are listed in hg.host_list
		for host in hg.host_list:
			host.delete()
		hg.delete()

	# delete dr
	dr = DiscoveryRule.get_by(name=discovery_rule_name)
	if dr: dr.delete()

	da = Action.get_by(name=discovery_action_name)
	if da: da.delete()

	ea = Action.get_by(name=escalation_action_name)
	if ea: ea.delete()

	return


def setup_global():
	# GLOBAL:
	#	update mediatype for email.
	############################### MAIL
	print "checking for MediaType Email"
	mediatype = MediaType.get_by(description="Email")
	if not mediatype:
		print "ERROR:  There is no defined media type for 'Email'"
		raise Exception("No Email Media type in Zabbix db")

	print "checking for correct configuration"
	mediatype = MediaType.get_by(smtp_email=config.from_email)
	if not mediatype:
		# NOTE: assumes smtp server is local to this machine.
		print "updating email server configuration"
		mediatype.smtp_server='localhost'
		mediatype.smtp_helo=".".join(config.MONITOR_HOSTNAME.split('.')[1:])
		mediatype.smtp_email=config.from_email

	############################# EMAIL
	mailtxt.reformat({'hostname' : config.MONITOR_HOSTNAME, 
					  'support_email' : config.support_email})

	############################### CENTRAL SERVER
	print "checking zabbix server host info"
	zabbixserver = Host.get_by(host="ZABBIX Server")
	if zabbixserver:
		print "UPDATING Primary Zabbix server entry"
		zabbixserver.host="MyPLC Server"
		zabbixserver.ip=config.MONITOR_IP
		zabbixserver.dns=config.MONITOR_HOSTNAME
		zabbixserver.useip=1

	############################ DEFAULT TEMPLATES
	# pltemplate - via web, xml import
	# TODO: os.system("curl --post default_templates.xml")

	##################### SCRIPTS 
	## TODO: add calls to check/reset the boot states.
	print "checking scripts"
	script1 = Script.find_or_create(name="RebootNode",
									set_if_new = {
										'command':"/usr/share/monitor-server/reboot.py {HOST.CONN}",
										'host_access':3 # r/w)
									})
	script2 = Script.find_or_create(name="NMap",
							set_if_new = {
								'command':"/usr/bin/nmap -A {HOST.CONN}",
								'host_access':2 # r/o)
						})
	return

def setup_site(loginbase, techemail, piemail, iplist):

	# TODO: Initially adding this info is ok. what about updates to users,
	# additional hosts, removed users from plc, 
	# TODO: send a message when host is discovered.
	# TODO: update 'discovered' hosts with dns name.
	# TODO: remove old nodes that are no longer in the plcdb.

	BI_WEEKLY_ESC_PERIOD = int(60*60*24)
	BI_WEEKLY_ESC_PERIOD = int(60) # testing...

	# User Group
	site_user_group = UsrGrp.find_or_create(name="%s_usergroup" % loginbase)
	for user in set(techemail + piemail):
		# USER
		u = User.find_or_create(alias=user, type=1,
								set_if_new={'passwd' : md5.md5(user).hexdigest()},
								exec_if_new=lambda obj: \
								obj.media_list.append( Media(mediatypeid=1, sendto=user)))

		if site_user_group not in u.usrgrp_list:
			u.append_group(site_user_group)

	# HOST GROUP
	plc_host_group = HostGroup.find_or_create(name="MyPLC Hosts")
	site_host_group = HostGroup.find_or_create(name="%s_hostgroup" % loginbase)
	plctemplate = Host.get_by(host="Template_Linux_PLHost")
	escalation_action_name = ESCALATION_ACTION_NAME % loginbase
	discovery_action_name = DISCOVERY_ACTION_NAME % loginbase
	discovery_rule_name = DISCOVERY_RULE_NAME % loginbase

	# ADD hg to ug
	if site_host_group not in site_user_group.hostgroup_list:
		site_user_group.append_hostgroup(site_host_group)

	# DISCOVERY RULE & CHECK
	dr = DiscoveryRule.find_or_create(name=discovery_rule_name,
			  delay=3600,
			  proxy_hostid=0,
			  set_if_new = {'iprange':iplist},
			  exec_if_new=lambda obj: \
			  	obj.discoverycheck_list.append( DiscoveryCheck(type=9, 
										key_="system.uname", ports=10050) )
			)
	if dr.iprange != iplist:
		if len(iplist) < 255:
			dr.iprange = iplist
		else:
			raise Exception("iplist length is too long!")
		

	# DISCOVERY ACTION for these servers
	a = Action.find_or_create(name=discovery_action_name,
			eventsource=defines.EVENT_SOURCE_DISCOVERY,
			status=defines.DRULE_STATUS_ACTIVE,
			evaltype=defines.ACTION_EVAL_TYPE_AND_OR)
	if len(a.actioncondition_list) == 0:
		a.actioncondition_list=[
					# Host IP Matches
					ActionCondition(
						conditiontype=defines.CONDITION_TYPE_DHOST_IP,
						operator=defines.CONDITION_OPERATOR_EQUAL,
						value=iplist),
					# AND, Service type is Zabbix agent
					ActionCondition(
						conditiontype=defines.CONDITION_TYPE_DSERVICE_TYPE,
						operator=defines.CONDITION_OPERATOR_EQUAL,
						value=defines.SVC_AGENT),
					# AND, Received system.uname value like 'Linux'
					ActionCondition(
						conditiontype=defines.CONDITION_TYPE_DVALUE,
						operator=defines.CONDITION_OPERATOR_LIKE,
						value="Linux"),
					# AND, Discovery status is Discover
					ActionCondition(
						conditiontype=defines.CONDITION_TYPE_DSTATUS,
						operator=defines.CONDITION_OPERATOR_EQUAL,
						value=defines.DOBJECT_STATUS_DISCOVER),
				]
				# THEN
		a.actionoperation_list=[
					# Add Host
					ActionOperation(
						operationtype=defines.OPERATION_TYPE_HOST_ADD,
						object=0, objectid=0,
						esc_period=0, esc_step_from=1, esc_step_to=1),
					# Add To Group PLC Hosts
					ActionOperation(
						operationtype=defines.OPERATION_TYPE_GROUP_ADD,
						object=0, objectid=plc_host_group.groupid,
						esc_period=0, esc_step_from=1, esc_step_to=1),
					# Add To Group LoginbaseSiteGroup
					ActionOperation(
						operationtype=defines.OPERATION_TYPE_GROUP_ADD,
						object=0, objectid=site_host_group.groupid,
						esc_period=0, esc_step_from=1, esc_step_to=1),
					# Link to Template 'Template_Linux_Minimal'
					ActionOperation(
						operationtype=defines.OPERATION_TYPE_TEMPLATE_ADD,
						object=0, objectid=plctemplate.hostid,
						esc_period=0, esc_step_from=1, esc_step_to=1),
				]
	else:
		# TODO: verify iplist is up-to-date
		pass

	# ESCALATION ACTION for these servers
	ea = Action.find_or_create(name=escalation_action_name,
			eventsource=defines.EVENT_SOURCE_TRIGGERS,
			status=defines.ACTION_STATUS_ENABLED,
			evaltype=defines.ACTION_EVAL_TYPE_AND_OR,
			esc_period=BI_WEEKLY_ESC_PERIOD,	# three days
			recovery_msg=1,
			set_if_new={
				'r_shortdata':"Thank you for maintaining {HOSTNAME}!",
				'r_longdata': mailtxt.thankyou_nodeup, }
			)
	if len(ea.actioncondition_list) == 0:
			# THEN this is a new entry
		print "SETTING UP ESCALATION ACTION"
		ea.actioncondition_list=[
				ActionCondition(conditiontype=defines.CONDITION_TYPE_TRIGGER_VALUE, 
								operator=defines.CONDITION_OPERATOR_EQUAL, 
								value=defines.TRIGGER_VALUE_TRUE),
				ActionCondition(conditiontype=defines.CONDITION_TYPE_TRIGGER_NAME, 
								operator=defines.CONDITION_OPERATOR_LIKE, 
								value="is unreachable"),
				ActionCondition(conditiontype=defines.CONDITION_TYPE_HOST_GROUP, 
								operator=defines.CONDITION_OPERATOR_EQUAL, 
								value=site_host_group.groupid),
			]
		ea.actionoperation_list=[
				# STAGE 1
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE,
					shortdata=mailtxt.nodedown_one_subject,
					longdata=mailtxt.nodedown_one,
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					esc_period=0, esc_step_to=3, esc_step_from=3, 
					operationcondition_list=[ OperationConditionNotAck() ] ),
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE,
					shortdata=mailtxt.nodedown_one_subject,
					longdata=mailtxt.nodedown_one,
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					esc_period=0, esc_step_to=7, esc_step_from=7, 
					operationcondition_list=[ OperationConditionNotAck() ] ),
				# STAGE 2
				ActionOperation(operationtype=defines.OPERATION_TYPE_COMMAND, 
					esc_step_from=10, esc_step_to=10, 
					esc_period=0,
					shortdata="",
					longdata="zabbixserver:/usr/share/monitor-server/checkslices.py {HOSTNAME} disablesite", 
					operationcondition_list=[ OperationConditionNotAck() ]),
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE, 
					shortdata=mailtxt.nodedown_two_subject,
					longdata=mailtxt.nodedown_two,
					esc_step_from=10, esc_step_to=10, 
					esc_period=0, 
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					operationcondition_list=[ OperationConditionNotAck() ] ), 
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE, 
					shortdata=mailtxt.nodedown_two_subject,
					longdata=mailtxt.nodedown_two,
					esc_step_from=14, esc_step_to=14, 
					esc_period=0, 
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					operationcondition_list=[ OperationConditionNotAck() ] ), 

				# STAGE 3
				ActionOperation(operationtype=defines.OPERATION_TYPE_COMMAND, 
					esc_step_from=17, esc_step_to=17, 
					esc_period=0, 
					shortdata="",
					longdata="zabbixserver:/usr/share/monitor-server/checkslices.py {HOSTNAME} disableslices", 
					# TODO: send notice to users of slices
					operationcondition_list=[ OperationConditionNotAck() ]),
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE, 
					shortdata=mailtxt.nodedown_three_subject,
					longdata=mailtxt.nodedown_three,
					esc_step_from=17, esc_step_to=17, 
					esc_period=0, 
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					operationcondition_list=[ OperationConditionNotAck() ] ), 
				# STAGE 4++
				ActionOperation(operationtype=defines.OPERATION_TYPE_COMMAND, 
					esc_step_from=21, esc_step_to=0, 
					esc_period=int(BI_WEEKLY_ESC_PERIOD*3.5),
					shortdata="",
					longdata="zabbixserver:/usr/share/monitor-server/checkslices.py {HOSTNAME} forever", 
					operationcondition_list=[ OperationConditionNotAck() ]),
				ActionOperation(operationtype=defines.OPERATION_TYPE_MESSAGE, 
					shortdata=mailtxt.nodedown_four_subject,
					longdata=mailtxt.nodedown_four,
					esc_step_from=21, esc_step_to=0, 
					esc_period=int(BI_WEEKLY_ESC_PERIOD*3.5),
					object=defines.OPERATION_OBJECT_GROUP, 
					objectid=site_user_group.usrgrpid, 
					operationcondition_list=[ OperationConditionNotAck() ] ), 
			]

if __name__ == "__main__":
	setup_global()
	session.flush()
