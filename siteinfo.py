#!/usr/bin/python

import plc
import auth
api = plc.PLC(auth.auth, auth.plc)

import soltesz
import reboot

import time
from model import *
from nodecommon import *

import config as configmodule

from config import config as cfg
from optparse import OptionParser

parser = OptionParser()
parser.set_defaults(site=None, 
					findbad=False,
					enable=False,
					disable=False
					)
parser.add_option("", "--site", dest="site", metavar="login_base", 
					help="The sitename to present")
parser.add_option("", "--findbad", dest="findbad", action="store_true", 
					help="Re-run findbad on the nodes we're going to check before acting.")
parser.add_option("", "--enable", dest="enable", action="store_true",
					help="")
parser.add_option("", "--disable", dest="disable", action="store_true",
					help="")
config = cfg(parser)
config.parse_args()

from unified_model import *
def color_sitestatus(status):
	if status == "good":
		return green(status)
	elif status == "down":
		return red(status)
	else:
		return status
		

def pf_print_siteinfo(sitename):
	pf = PersistFlags(sitename, 1, db='site_persistflags')
	if pf.checkattr('last_changed'):
		print "   Checked: %s" % diff_time(pf.last_checked)
		print "\t status | nodes up / total | last_change"
		print "\t   %6s | %8s / %5s | %s" % \
			( color_sitestatus(pf.status), pf.nodes_up, pf.nodes_total, diff_time(pf.last_changed) )
	else:
		print "no  such site in pf"
	del pf


def plc_print_siteinfo(plcsite):
	print ""
	print "   Checked: %s" % time.ctime()
	print "\t login_base    | used / max | enabled | last_updated "
	print "\t %13s | %4s / %3s | %7s | %12s" % \
			(plcsite['login_base'], 
			 len(plcsite['slice_ids']),
			 plcsite['max_slices'],
			 plcsite['enabled'],
			 diff_time(plcsite['last_updated']))

	print ""
	nodes = api.GetNodes(plcsite['node_ids'])
	print "   Checked: %s" % time.ctime()
	print "\t                               host     | state | obs   |   created   |   updated   | last_contact "
	for plcnode in nodes:
		fbnode = fb['nodes'][plcnode['hostname']]['values']
		plcnode['state'] = color_boot_state(get_current_state(fbnode))
		print "\t  %37s |  %5s |  %5s | %11.11s | %11.11s | %12s " % \
		(plcnode['hostname'], color_boot_state(plcnode['boot_state']), plcnode['state'], 
			diff_time(plcnode['date_created']), diff_time(plcnode['last_updated']), 
		diff_time(plcnode['last_contact']))


fb = soltesz.dbLoad("findbad")
act_all = soltesz.dbLoad("act_all")

for site in config.args:
	config.site = site

	plc_siteinfo = api.GetSites({'login_base': config.site})[0]
	url = "https://www.planet-lab.org/db/sites/index.php?site_pattern="
	plc_siteinfo['url'] = url + plc_siteinfo['login_base']

	if config.findbad:
		# rerun findbad with the nodes in the given nodes.
		import os
		file = "findbad.txt"
		nodes = api.GetNodes(plc_siteinfo['node_ids'], ['hostname'])
		nodes = [ n['hostname'] for n in nodes ]
		configmodule.setFileFromList(file, nodes)
		os.system("./findbad.py --cachenodes --debug=0 --dbname=findbad --increment --nodelist %s" % file)

	print "%(login_base)s %(url)s" % plc_siteinfo
	pf_print_siteinfo(config.site)
	plc_print_siteinfo(plc_siteinfo)

	if config.enable:
		api.UpdateSite(config.site, {'enabled' : True})
	if config.disable:
		api.UpdateSite(config.site, {'enabled' : False})