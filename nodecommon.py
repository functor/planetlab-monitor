
import struct
import reboot
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
	import plc

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

def diff_time(timestamp):
	import math
	now = time.time()
	if timestamp == None:
		return "unknown"
	diff = now - timestamp
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
	elif diff < 60*60*24*7: # sec in week
		t = diff / (60*60*24)
		t_str = "%s days ago" % int(math.ceil(t))
	elif diff <= 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*7)
		t_str = "%s wks ago" % int(math.ceil(t))
	elif diff > 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*30)
		t_str = "%s mnths ago" % int(t)
	return t_str

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

	return "%(hostname)-42s %(boot_state)8s %(current)5s %(pcu)6s %(key)20.20s... %(kernel)43s %(lastupdate)12s " % node

from model import *
import database

def node_end_record(node):
	act_all = database.dbLoad("act_all")
	if node not in act_all:
		del act_all
		return False

	if len(act_all[node]) == 0:
		del act_all
		return False

	a = Action(node, act_all[node][0])
	a.delField('rt')
	a.delField('found_rt_ticket')
	a.delField('second-mail-at-oneweek')
	a.delField('second-mail-at-twoweeks')
	a.delField('first-found')
	rec = a.get()
	rec['action'] = ["close_rt"]
	rec['category'] = "UNKNOWN"
	rec['stage'] = "monitor-end-record"
	rec['time'] = time.time() - 7*60*60*24
	act_all[node].insert(0,rec)
	database.dbDump("act_all", act_all)
	del act_all
	return True

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
