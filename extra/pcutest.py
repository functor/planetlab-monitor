#!/usr/bin/python

from monitor.wrapper import plc
import sys
import time

from monitor import config

api06 = plc.PLC(plc.Auth(config.API06_AUTH_USER, config.API06_AUTH_PASSWORD).auth, config.API06_SERVER)
api06 = plc.api

if True:
	# update old model names to new model names.
	update = {	'AP79xx' : 'APCControl13p13',
				'Masterswitch' : 'APCControl13p13',
				'DS4-RPC' : 'BayTech',
				'IP-41x_IP-81x' : 'IPAL',
				'DRAC3' : 'DRAC',
				'DRAC4' : 'DRAC',
				'ePowerSwitch' : 'ePowerSwitchOld',
				'ilo2' : 'HPiLO',
				'ilo1' : 'HPiLO',
				'PM211-MIP' : 'PM211MIP',
				'AMT2.5' : 'IntelAMT',
				'AMT3.0' : 'IntelAMT',
				'WTI_IPS-4' : 'WTIIPS4',
				'unknown'  : 'ManualPCU',
				'DRAC5'	: 'DRAC',
				'ipmi'	: 'OpenIPMI',
				'bbsemaverick' : 'BlackBoxPSMaverick',
				'manualadmin'  : 'ManualPCU',
			}
	pcus = api06.GetPCUs()
	for pcu in pcus:
		if pcu['model'] in update.keys():
			new_model = update[pcu['model']]
			values = pcu

			if values['pcu_id'] in [1102,1163,1055,1111,1231,1113,1127,1128,1148]:
				new_model = 'APCControl12p3'
			elif values['pcu_id'] in [1110,86]:
				new_model = 'APCControl1p4'
			elif values['pcu_id'] in [1221,1225,1220,1192]:
				new_model = 'APCControl121p3'
			elif values['pcu_id'] in [1173,1240,47,1363,1405,1401,1372,1371]:
				new_model = 'APCControl121p1'
			elif values['pcu_id'] in [1056,1237,1052,1209,1002,1008,1041,1013,1022]:
				new_model = 'BayTechCtrlC'
			elif values['pcu_id'] in [93]:
				new_model = 'BayTechRPC3NC'
			elif values['pcu_id'] in [1057]:
				new_model = 'BayTechCtrlCUnibe'
			elif values['pcu_id'] in [1012]:
				new_model = 'BayTechRPC16'
			elif values['pcu_id'] in [1089, 1071, 1046, 1035, 1118]:
				new_model = 'ePowerSwitchNew'

			print "Updating %s \tfrom model name %s to %s" % (pcu['pcu_id'], pcu['model'], new_model)
			api06.UpdatePCU(pcu['pcu_id'], {'model' : new_model})

if False:
	pcus = api06.GetPCUs()
	for pcu in pcus:
		api06.AddNodeToPCU(1, pcu['pcu_id'], 1)

if False:
	pcu_types = [
			 {'model': 'APCControl12p3',
		  	  'name': 'APC AP79xx or Masterswitch (sequence 1-2-port-3)', },
			 {'model': 'APCControl1p4',
		  	  'name': 'APC AP79xx or Masterswitch (sequence 1-port-4)', },
			 {'model': 'APCControl121p3',
		  	  'name': 'APC AP79xx or Masterswitch (sequence 1-2-1-port-3)', },
			 {'model': 'APCControl121p1',
		  	  'name': 'APC AP79xx or Masterswitch (sequence 1-2-1-port-1)', },
			 {'model': 'APCControl13p13',
		  	  'name': 'APC AP79xx or Masterswitch (sequence 1-3-port-1-3)', },

			 {'model': 'BayTechRPC3NC', 
			  'name': 'BayTech with prompt RPC3-NC>', },
			 {'model': 'BayTechRPC16', 
			  'name': 'BayTech with prompt RPC-16>', },
			 {'model': 'BayTech', # 'DS4-RPC',
			  'name': 'BayTech with prompt DS-RPC>', },
			 {'model': 'BayTechCtrlC', 
			  'name': 'BayTech Ctrl-C, 5, then with prompt DS-RPC>', },
			 {'model': 'BayTechCtrlCUnibe', 
			  'name': 'BayTech Ctrl-C, 3, then with prompt DS-RPC>', },

			 {'model': 'BlackBoxPSMaverick',
			  'name': 'BlackBoxPSMaverick Web based controller'},

			 {'model': 'IPAL',  # 'IP-41x_IP-81x',
			  'name': 'IPAL - Dataprobe IP-41x & IP-81x', },
			 {'model': 'DRAC',
			  'name': 'DRAC - Dell RAC Version 3 or 4', },
			 {'model': 'ePowerSwitchNew',
			  'name': 'ePowerSwitch Newer Models 1/4/8x', },
			 {'model': 'ePowerSwitchOld',
			  'name': 'ePowerSwitch Older Models 1/4/8x', },

			 {'model': 'HPiLO',  # ilo2
			  'name': 'HP iLO v1 or v2 (Integrated Lights-Out)', },

			 {'model': 'IntelAMT', # 'AMT3.0',
			  'name': 'Intel AMT v2.5 or v3.0 (Active Management Technology)', },

			 {'model': 'IPMI',
			  'name': 'IPMI - Intelligent Platform Management Interface', },

			 {'model': 'PM211MIP',
			  'name': 'Infratec PM221-MIP', },

			 {'model': 'WTIIPS4', #WTI-IPS-4
			  'name': 'Western Telematic (WTI IPS-4)', },

			 {'model': 'ManualPCU',
			  'name': 'Manual Administrator Operation (choose if model unknown)', },
			  ]

	# Get all model names
	pcu_models = [type['model'] for type in api06.GetPCUTypes()]
	for type in pcu_types:
		if 'pcu_protocol_types' in type:
			protocol_types = type['pcu_protocol_types']
			# Take this value out of the struct.
			del type['pcu_protocol_types']
		else:
			protocol_types = []
		if type['model'] not in pcu_models:
			# Add the name/model info into DB
			id = api06.AddPCUType(type)
			# for each protocol, also add this.
			for ptype in protocol_types:
				api06.AddPCUProtocolType(id, ptype)

#for type in api06.GetPCUTypes():
#	print "removing %s" % type['model']
#	api06.DeletePCUType(type['pcu_type_id'])
		
