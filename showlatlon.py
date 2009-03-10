#!/usr/bin/python

import plc
api = plc.getAuthAPI()

import sys
import reboot
from datetime import datetime, timedelta

import database
import comon
from nodecommon import color_pcu_state, datetime_fromstr
from nodehistory import get_filefromglob
import time

# region
# total
# up
# up with good hardware
# up with good hardware & functional pcu

#cm_url="http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=formatcsv&dumpcols='name,cpuspeed,memsize,disksize'"
#cm = database.if_cached_else(1, "cmhardware", lambda : comon.comonget(cm_url))

def gethardwarequality(nodename, fb):
	if nodename in fb['nodes'] and 'comonstats' in fb['nodes'][nodename]['values']:
		cstat = fb['nodes'][nodename]['values']['comonstats']
		for field in ['cpuspeed', 'memsize', 'disksize']:
			if field not in cstat: cstat[field] = "null"

		if cstat['cpuspeed'] != "null" and float(cstat['cpuspeed']) < 2.2:
			return "BAD" # "cpu_slow",
		if cstat['memsize'] != "null" and float(cstat['memsize']) < 2.8:
			return "BAD" # "mem_small",
		if cstat['disksize'] != "null" and float(cstat['disksize']) < 300.0:
			return "BAD" # "disk_small",

		if cstat['disksize'] == "null" and \
		   cstat['cpuspeed'] == "null" and \
		   cstat['memsize'] == "null":
			return "N/A"

		try:
			if  float(cstat['cpuspeed']) >= 2.2 and \
				float(cstat['memsize']) >= 2.8 and \
				(cstat['disksize'] == "null" or float(cstat['disksize']) >= 300.0):
				return "A-OK"
		except:
			print cstat

		return "ZOO"
	else:
		return "N/A"

def addtostats(stats, a):
	if a['cc'] not in stats:
		stats[a['cc']] = {'total' : 0,
		                  'up' : 0,
						  'goodhw': 0,
						  'pcuok' : 0}
	
	stats[a['cc']]['total'] += 1
	if a['status'] == "boot":
		stats[a['cc']]['up'] += 1  
		if a['hardware'] == "A-OK":
			stats[a['cc']]['goodhw'] += 1 
			if a['pcuok'] == "PCUOK  " or a['pcuok'] == "PCUA-OK":
				stats[a['cc']]['pcuok'] += 1

def main():

	stats = {}
	path = "archive-pdb"
	archive = database.SPickle(path)

	if len(sys.argv) > 2:
		timestr = sys.argv[1]
		format = sys.argv[2]
		begin = timestr
	else:
		format = "%Y-%m-%d"
		begin = time.strftime(format)

	d = datetime_fromstr(begin)
	fbstr = get_filefromglob(d, "production.findbad")[0]
	fbpcustr = get_filefromglob(d, "production.findbadpcus")[0]

	l_plcnodes = database.dbLoad("l_plcnodes")
	l_plcsites = database.dbLoad("l_plcsites")
	lb2hn = database.dbLoad("plcdb_lb2hn")
	fb = archive.load(fbstr) 
	fbpcu = archive.load(fbpcustr)
	reboot.fb = fbpcu

	results = []
	# COLLECT nodegroups, nodes and node lists
	for site in l_plcsites:
		CC="none"
		if site['login_base'] in lb2hn:
			nodes = lb2hn[site['login_base']]
			for node in nodes:
				hostname = node['hostname']
				fields = hostname.split(".")
				if len(fields[-1]) == 2:
					CC=fields[-1]
				elif fields[-1] == "edu":
					CC="usedu"
				elif site['login_base'] == "ft":
					CC="fr"
				elif site['login_base'] == "ntu":
					CC="tw"
				elif site['login_base'] in ["mcgill", "canarieottawa", 'canariecalgary',
											'canariehalifax', 'canariemontreal',
											'canarietoronto', 'canariewinnipeg']:
					CC="ca"
				elif site['login_base'] in ["plcoloclarasanti", "plcoloclarasaopa",
											"plcoloclarabueno", "plcoloclaratijua", 
											"plcoloclarapanam"]:
					CC="southamerica"
				elif site['login_base'] in ["plcoloamst", 'cwi']:
					CC="nl"
				elif site['login_base'] == "urv":
					CC="es"
				elif site['login_base'] == "ncl":
					CC="uk"
				elif site['login_base'] == "waterford":
					CC="ie"
				elif site['login_base'] in ["kisti", "snummlab"]:
					CC="kr"
				elif site['login_base'] == "astri":
					CC="cn"
				elif fields[-1] in [ "org", "net" ]:
					CC="usorg"
				elif fields[-1] == "com":
					CC="uscom"
				else:
					CC=fields[-1]

				if hostname in fb['nodes']:
					if 'state' in fb['nodes'][hostname]['values']:
						state = fb['nodes'][hostname]['values']['state'].lower()
					else:
						state = "unknown"

					args = {'cc': CC, 
						'site' : site['login_base'],
						'host' : hostname,
						'status' : state,
						'hardware' : gethardwarequality(hostname, fb),
						'pcuok' : color_pcu_state(fb['nodes'][hostname]['values']) }
					#except:
					#	print args
					#	print fb['nodes'][hostname]['values']
					results.append("%(cc)7s %(status)8s %(hardware)8s %(pcuok)8s %(site)15s %(host)42s " % args)
					addtostats(stats, args)
		else:
			site['latitude'] = -2
			site['longitude'] = -2

		#print "%4s %20s %8s %8s" % (CC, site['login_base'], site['latitude'], site['longitude'])

	regions = { 'mideast'	: ['cy', 'gr', 'il', 'in', 'lb', 'pk'],
				'ca'        : ['ca'],
				'usa'		: ['pr','us', 'uscom', 'usedu', 'usorg'],
				'europe'	: ['at','ch','cz','be', 'de', 'dk', 
							   'es','fi', 'fr', 'hu', 'ie', 'is', 'it','nl',
							   'no', 'pl', 'pt', 'se', 'tr', 'uk'],
				'asia'		: ['cn','hk','jp','kr', 'ru', 'sg', 'si','tw',],
				'australia': ['au', 'nz',],
				'southam'	: ['ar','br','southamerica','uy', 've'],
				}
	# fold stats
	statsfold = {}
	for key in regions.keys():
		statsfold[key] = {'total' : 0, 'up' : 0, 
						'goodhw': 0, 'pcuok' : 0}

	totaltotal = {	'total' : 0, 'up' : 0, 
					'goodhw': 0, 'pcuok' : 0}
	# for all of the cc stats
	for cc in stats.keys():
		# search for the cc in the regions dict
		for region in regions:
			# if the cc is assigned to a region
			if cc in regions[region]:
				# add all values in cc stats to that region
				for key in statsfold[region]:
					statsfold[region][key] += stats[cc][key]
					totaltotal[key] += stats[cc][key]

	# print folded stats
	print "       REGION | total | up  |& goodhw |& pcuok "
	for region in statsfold.keys():
		statsfold[region]['region'] = region
		print "%(region)13s | %(total)5s | %(up)3s | %(goodhw)7s | %(pcuok)3s" % statsfold[region]
	print "       totals | %(total)5s | %(up)3s | %(goodhw)7s | %(pcuok)3s" % totaltotal


	print "      Region  | total | up  |& goodhw |& pcuok "
	for region in stats.keys():
		stats[region]['region'] = region
		print "%(region)13s | %(total)5s | %(up)3s | %(goodhw)7s | %(pcuok)3s" % stats[region]

	for line in results:
		print line
		
if __name__ == "__main__":
	try:
		main()
	except IOError:
		pass
