#!/usr/bin/python

#import database
from monitor.wrapper import plccache
import monitor.parser as parsermodule
import sys
from reboot import pcu_name, get_pcu_values

import sys

def print_dict(dict):
	for key in dict.keys():
		print "%30s : %s" % (key, dict[key])

pculist = plccache.l_pcus 
for pcu in pculist:
	if 'model' in pcu and pcu['model'] == None:
		continue

	if True: 
		host = pcu_name(pcu)
		values = get_pcu_values(pcu['pcu_id'])
		#if 'port_status' not in values:
		#	portstatus = ""
		#else:
		#	if values['reboot_trial_status'] == 0 or (not isinstance(values['reboot_trial_status'],int) and values['reboot_trial_status'].find("error") >= 0):
		#		portstatus = "22:%(22)s 23:%(23)s" % values['port_status']
		#if 'reboot_trial_status' in values and (values['reboot_trial_status'] == 0 or values['reboot_trial_status'] == "0"):
		print "%6d: %10s %20s %50s reboot:%s" % (pcu['pcu_id'], pcu['model'], pcu['password'], "%s@%s" % (pcu['username'], host), values['reboot_trial_status'])

#database.dbDump("pculist", pculist, 'php')
