#!/usr/bin/python

# Register the monitor user with your instance of PLC.

# NOTE: Need some way of collecting information about where the target PLC is
# located.  Clearly this script needs to be run by someone with ADMIN
# privilges in order to setup an ssh key, add a user, and upload the key to
# the user, make the user a member of the PLC site, etc.

import auth
import plc
import sys
import os

def filevalue(filename):
	f = open(filename, 'r')
	ret = f.read()
	f.close()
	return ret

api = plc.PLC(auth.auth, auth.plc)

# Add user : 'Site', 'Assistant', 'monitor@planet-lab.org'
person = { 'first_name': 'Site', 
			'last_name' : 'Assistant',
			'email' : 'monitor@planet-lab.org',
			'url' : 'http://monitor.planet-lab.org', }
ret = api.GetPersons(person['email'], ['person_id'])
if len(ret) == 0:
	# entry does not exist in Database, so Add it.
	id = api.AddPerson(person)
else:
	# use existing entry.
	id = ret[0]['person_id']

# Generate ssh key.
if not os.path.exists("%s.pub" % keyname):
	keyname = "monitor_rsa"
	print "Creating ssh key pair for %s" % person['email']
	os.system("ssh-keygen -t rsa -b 2048 -f %s < /dev/null" % keyname)

if not os.path.exists("%s.pub" % keyname):
	print "Error generating public/private key pair."
	print "Please try running the command manually."
	print "ssh-keygen -t rsa -b 2048 -f %s < /dev/null" % keyname
	sys.exit(1)

# Upload key.
keys = api.GetKeys({ 'person_id' : id })
if len(keys) == 0:	
	key_id = api.AddPersonKey(id, { 'key_type' : 'ssh', 
									'key' : filevalue("%s.pub" % keyname)} )
else:
	key_id = keys[0]['key_id']

# Copy private key into the directory from which the monitor scripts will be
# 	run/activated.
### os.system("cp %s /usr/local/monitor/keys" % keyname)

# Add cron entries to periodically poll nodes, and PCUs.
### os.system("crontab ---")
