#!/usr/bin/python

import plc
import auth
import sys
import time

email_list = [ 'monitor@planet-lab.org', 
			 # 'soltesz@cs.princeton.edu',
			 # 'justin@cs.arizona.edu',
             # 'bakers@cs.arizona.edu',
             # 'jhh@cs.arizona.edu',
        	 # 'mfreed@cs.nyu.edu',
         	 # 'kyoungso@cs.princeton.edu',
		 	 # 'nspring@cs.umd.edu',
        	 # 'vivek@cs.princeton.edu',
		]

api   = plc.PLC(auth.auth, auth.plc)
api06 = plc.PLC(auth.auth06, auth.plc06)


# add planetlab-15.cs.princeton.edu, and use the key on the CD.
id = api06.AddNode(1, {'boot_state': 'rins', 'model': 'Dell Optiplex',
						  'hostname' : 'planetlab-15.cs.princeton.edu',
						  'version' : '3.3'})
api06.AddNodeNetwork(id, {'ip': '128.112.139.39',
								  'type' : 'ipv4',
								  'is_primary' : True,
								  'method' : 'dhcp', })
api06.UpdateNode(id, {'key': "wptNagk8SgRxzN1lXfKMAjUYhQbOBymKnKg9Uv0LwGM"})


#print "adding vsys attributes"
#api06.AddSliceAttribute('princeton_slicestat', 'vsys', 'pl-ps')
#api06.AddSliceAttribute('princeton_slicestat', 'vsys', 'vtop')
#api06.AddSliceAttribute('pl_netflow', 'vsys', 'pfmount')

#print "preserve princeton_chopstix"

#sys.exit(1)

#attr_types   = api.GetSliceAttributeTypes()
#attr_types06 = api06.GetSliceAttributeTypes()
#attr_types06_names = [a['name'] for a in attr_types06]
#for type in attr_types:
#    if type['name'] not in attr_types06_names:
#        print "adding %s " % type
#        api06.AddSliceAttributeType(type)
def person_exists(user):
    try:
        x = api06.GetPersons({'email':user['email']})
        if len(x) == 0:
            return False
        else:
            return True
    except:
        return False

def site_exists(site):
    try:
        x = api06.GetSites({'login_base':site['login_base']})
        if len(x) == 0:
            return False
        else:
            return True
    except:
        return False

def slice_exists(slice):
    try:
        x = api06.GetSlices({'name':slice['name']})
        if len(x) == 0:
            return False
        else:
            return True
    except:
        return False

# Renew  slices
slices = api06.GetSlices()
for slice in slices:
	print "Updating expiration of %s" % slice['name']
	api06.UpdateSlice(slice['name'], {'expires': int(time.time()) + 7*24*60*60})

#sys.exit(1)

for email in email_list:
    user = api.GetPersons({'email': email})
    if len(user) == 0:
        print "User not found: %s" % email
        continue

    user = user[0]

    print "adding person %s " % user['email']
    if not person_exists(user):
        api06.AddPerson(user)

        api06.UpdatePerson(email, {'enabled': True})

        print "adding person keys %s " % user['email']
        key = api.GetKeys({'person_id': user['person_id']})[0]
        key06 = {'key': key['key'], 'key_type': key['key_type']}
        api06.AddPersonKey(user['email'], key06)

        print "updating person roles: ",
        for role in user['roles']:
            print "%s" % role,
            api06.AddRoleToPerson(role, user['email'])
            sys.stdout.flush()
        print ""

    sites = api.GetSites(user['site_ids'])
    print "Adding sites:",
    for site in sites:
        if not site_exists(site):
            print "%s" % site['login_base'],
            api06.AddSite(site)
            api06.AddPersonToSite(user['email'], site['login_base'])
            sys.stdout.flush()
    print ""

    nodes = api06.GetNodes()
    slices = api.GetSlices(user['slice_ids'])
    for slice in slices:
        # create slice
        no_add = True
        if not slice_exists(slice):
            print "Adding slice %s" % slice['name']
            try: 
                api06.AddSlice(slice)
                attr = api.GetSliceAttributes({'slice_attribute_id' : 
                                            slice['slice_attribute_ids']})
                print "adding attributes:",
                added_attr = []
                for a in attr:
                    print "%s" % a['name'],
                    #if a['name'] not in added_attr:
                    api06.AddSliceAttribute(slice['name'], a['name'], a['value'])
                    #    added_attr.append(a['name'])
                    sys.stdout.flush()
                print ""
            except:
                no_add = False
                print "error with ", slice['name']

        if no_add:
            print "adding nodes and %s to slice %s" % (user['email'], slice['name'])
            # add all api06 nodes to slice
            api06.AddSliceToNodes(slice['name'], [n['hostname'] for n in nodes])
            # add user to slice
            api06.AddPersonToSlice(user['email'], slice['name'])
