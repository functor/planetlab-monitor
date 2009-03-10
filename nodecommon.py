
import struct
import reboot
import time
import util.file
import plc
from datetime import datetime 
from monitor import database
from unified_model import PersistFlags
esc = struct.pack('i', 27)
RED  	= esc + "[1;31m"
GREEN	= esc + "[1;32m"
YELLOW	= esc + "[1;33m"
BLUE	= esc + "[1;34m"
LIGHTBLUE	= esc + "[1;36m"
NORMAL  = esc + "[0;39m"

def red(str):
	return RED + str + NORMAL

def yellow(str):
	return YELLOW + str + NORMAL

def green(str):
	return GREEN + str + NORMAL

def lightblue(str):
	return LIGHTBLUE + str + NORMAL

def blue(str):
	return BLUE + str + NORMAL

def get_current_state(fbnode):
	if 'state' in fbnode:
		state = fbnode['state']
	else:
		state = "none"
	l = state.lower()
	if l == "debug": l = 'dbg '
	return l

def color_pcu_state(fbnode):

	if 'plcnode' in fbnode and 'pcu_ids' in fbnode['plcnode'] and len(fbnode['plcnode']['pcu_ids']) > 0 :
		values = reboot.get_pcu_values(fbnode['plcnode']['pcu_ids'][0])
		if values == None:
			return fbnode['pcu']
	else:
		if 'pcu' not in fbnode:
			return 'NOPCU'
		else:
			return fbnode['pcu']

	if 'reboot' in values:
		rb = values['reboot']
		if rb == 0 or rb == "0":
			return fbnode['pcu'] + "OK  "
			#return fbnode['pcu'] + "OK  "
			#return green(fbnode['pcu'])
		elif "NetDown" == rb  or "Not_Run" == rb:
			return fbnode['pcu'] + "DOWN"
			#return yellow(fbnode['pcu'])
		else:
			return fbnode['pcu'] + "BAD "
			#return red(fbnode['pcu'])
	else:
		#return red(fbnode['pcu'])
		return fbnode['pcu'] + "BAD "

def color_boot_state(l):
	if    l == "dbg": return yellow("debg")
	elif  l == "dbg ": return yellow("debg")
	elif  l == "diag": return lightblue(l)
	elif  l == "disable": return red("dsbl")
	elif  l == "down": return red(l)
	elif  l == "boot": return green(l)
	elif  l == "rins": return blue(l)
	else:
		return l

def diff_time(timestamp, abstime=True):
	import math
	now = time.time()
	if timestamp == None:
		return "unknown"
	if abstime:
		diff = now - timestamp
	else:
		diff = timestamp
	# return the number of seconds as a difference from current time.
	t_str = ""
	if diff < 60: # sec in min.
		t = diff / 1
		t_str = "%s sec ago" % int(math.ceil(t))
	elif diff < 60*60: # sec in hour
		t = diff / (60)
		t_str = "%s min ago" % int(math.ceil(t))
	elif diff < 60*60*24: # sec in day
		t = diff / (60*60)
		t_str = "%s hrs ago" % int(math.ceil(t))
	elif diff < 60*60*24*14: # sec in week
		t = diff / (60*60*24)
		t_str = "%s days ago" % int(math.ceil(t))
	elif diff <= 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*7)
		t_str = "%s wks ago" % int(math.ceil(t))
	elif diff > 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*30)
		t_str = "%s mnths ago" % int(t)
	return t_str

def getvalue(fb, path):
    indexes = path.split("/")
    values = fb
    for index in indexes:
        if index in values:
            values = values[index]
        else:
            return None
    return values

def nodegroup_display(node, fb, conf=None):
	if node['hostname'] in fb['nodes']:
		node['current'] = get_current_state(fb['nodes'][node['hostname']]['values'])
	else:
		node['current'] = 'none'

	if fb['nodes'][node['hostname']]['values'] == []:
		return ""

	s = fb['nodes'][node['hostname']]['values']['kernel'].split()
	if len(s) >=3:
		node['kernel'] = s[2]
	else:
		node['kernel'] = fb['nodes'][node['hostname']]['values']['kernel']
		
	if '2.6' not in node['kernel']: node['kernel'] = ""
	if conf and not conf.nocolor:
	    node['boot_state']	= color_boot_state(node['boot_state'])
	    node['current'] 	= color_boot_state(node['current'])
	#node['boot_state']	= node['boot_state']
	#node['current'] 	= node['current']
	node['pcu'] = fb['nodes'][node['hostname']]['values']['pcu']
	node['lastupdate'] = diff_time(node['last_contact'])
	pf = PersistFlags(node['hostname'], 1, db='node_persistflags')
	try:
		node['lc'] = diff_time(pf.last_changed)
	except:
		node['lc'] = "err"
	ut = fb['nodes'][node['hostname']]['values']['comonstats']['uptime']
	if ut != "null":
		ut = diff_time(float(fb['nodes'][node['hostname']]['values']['comonstats']['uptime']), False)
	node['uptime'] = ut

	return "%(hostname)-42s %(boot_state)8s %(current)5s %(pcu)6s %(key)10.10s... %(kernel)35.35s %(lastupdate)12s, %(lc)s, %(uptime)s" % node

def datetime_fromstr(str):
	if '-' in str:
		try:
			tup = time.strptime(str, "%Y-%m-%d")
		except:
			tup = time.strptime(str, "%Y-%m-%d-%H:%M")
	elif '/' in str:
		tup = time.strptime(str, "%m/%d/%Y")
	else:
		tup = time.strptime(str, "%m/%d/%Y")
	ret = datetime.fromtimestamp(time.mktime(tup))
	return ret

def get_nodeset(config):
	"""
		Given the config values passed in, return the set of hostnames that it
		evaluates to.
	"""
	api = plc.getAuthAPI()
	l_nodes = database.dbLoad("l_plcnodes")

	if config.nodelist:
		f_nodes = util.file.getListFromFile(config.nodelist)
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.node:
		f_nodes = [config.node]
		l_nodes = filter(lambda x: x['hostname'] in f_nodes, l_nodes)
	elif config.nodegroup:
		ng = api.GetNodeGroups({'name' : config.nodegroup})
		l_nodes = api.GetNodes(ng[0]['node_ids'], ['hostname'])
	elif config.site:
		site = api.GetSites(config.site)
		l_nodes = api.GetNodes(site[0]['node_ids'], ['hostname'])
		
	l_nodes = [node['hostname'] for node in l_nodes]

	# perform this query after the above options, so that the filter above
	# does not break.
	if config.nodeselect:
		fb = database.dbLoad("findbad")
		l_nodes = node_select(config.nodeselect, fb['nodes'].keys(), fb)

	return l_nodes
	
def email_exception(content=None):
	import config
	from unified_model import Message
	import traceback
	msg=traceback.format_exc() 
	if content:
		msg = content + "\n" + msg
	m=Message("exception running monitor", msg, False)
	m.send([config.cc_email])
	return
