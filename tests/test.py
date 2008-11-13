#!/usr/bin/python

from monitor import database
import os
import time
from unified_model import *

today = time.time()
four_days_ago = today - 60*60*24*4
eight_days_ago = today - 60*60*24*8

def reset_time(hostname, new_time):
	# update act_all entry
	act_all = database.dbLoad("act_all") 
	act_all[hostname][0]['time'] = new_time 
	database.dbDump("act_all", act_all) 
	# update message timer.
	m = PersistMessage(hostname, "d", "e", True, db='monitor_persistmessages') 
	m.actiontracker.time = new_time 
	m.save()

def get_record(hostname):
	act_all = database.dbLoad("act_all") 
	rec = act_all[hostname][0]
	return rec
	

def bring_node_down(hostname):
	fb = database.dbLoad("findbad")
	fb['nodes'][hostname]['values'].update({'category' : 'ERROR', 
									'kernel' : '',
									'state' : 'DOWN', 'ssh' : 'NOSSH'})
	database.dbDump("findbad", fb)
	# update message timer.
	m = PersistMessage(hostname, "d", "e", True, db='monitor_persistmessages') 
	m.actiontracker.time = time.time() - 60*60*24*4
	m.save()

def bring_node_up(hostname):
	fb = database.dbLoad("findbad")
	fb['nodes'][hostname]['values'].update({'category' : 'ALPHA', 
									'kernel' : 'a b 2.6.22.19-vs2.3.0.34.24.planetlab', 
									'state' : 'BOOT', 'ssh' : 'SSH'})
	database.dbDump("findbad", fb)
	# update message timer.
	m = PersistMessage(hostname, "d", "e", True, db='monitor_persistmessages') 
	m.actiontracker.time = time.time() - 60*60*24*4
	m.save()

#bring_node_down('fakenode.cs.princeton.edu')

node_end_record('fakenode.cs.princeton.edu')
node_end_record('eggplant.cs.princeton.edu')
bring_node_down('eggplant.cs.princeton.edu')
bring_node_down('fakenode.cs.princeton.edu')
os.system("./nodebad.py --increment --site monitorsite")
os.system("./sitebad.py --increment --site monitorsite")

# week one
# initial
os.system("./grouprins.py --force --reboot --mail=1 \
 --nodeselect 'hostname=(eggplant|fakenode).cs.princeton.edu&&state=DOWN' \
 --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")
reset_time('eggplant.cs.princeton.edu', four_days_ago)
reset_time('fakenode.cs.princeton.edu', four_days_ago)
# second
os.system("./grouprins.py --force --reboot --mail=1 \
 --nodeselect 'hostname=(eggplant|fakenode).cs.princeton.edu&&state=DOWN' \
 --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")
reset_time('eggplant.cs.princeton.edu', eight_days_ago)
reset_time('fakenode.cs.princeton.edu', eight_days_ago)
# week two
# transition.
os.system("./grouprins.py --force --reboot --mail=1 \
 --nodeselect 'hostname=(eggplant|fakenode).cs.princeton.edu&&state=DOWN' \
 --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")
reset_time('eggplant.cs.princeton.edu', four_days_ago)
reset_time('fakenode.cs.princeton.edu', four_days_ago)
# second for week two
os.system("./grouprins.py --force --reboot --mail=1 \
 --nodeselect 'hostname=(eggplant|fakenode).cs.princeton.edu&&state=DOWN' \
 --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")
reset_time('eggplant.cs.princeton.edu', eight_days_ago)
reset_time('fakenode.cs.princeton.edu', eight_days_ago)
# week three
 # transition
os.system("./grouprins.py --force --reboot --mail=1 \
 --nodeselect 'hostname=(eggplant|fakenode).cs.princeton.edu&&state=DOWN' \
 --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")

# node is up.
bring_node_up("eggplant.cs.princeton.edu")
bring_node_up("fakenode.cs.princeton.edu")
os.system("./nodebad.py --increment --site monitorsite")
os.system("./sitebad.py --increment --site monitorsite")

os.system("./grouprins.py --force --reboot --mail=1 --nodeselect 'hostname=eggplant.cs.princeton.edu&&state=BOOT' --stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.24.planetlab'")

