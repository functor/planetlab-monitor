#!/usr/bin/python

import os
import sys
import string
import time

import getopt
import sys
import os
import xml, xmlrpclib
from getpass import getpass
from operator import attrgetter, itemgetter

def get_plc_api(target, url, username, password, expires, debug_mode):
    # Either read session from disk or create it and save it for later
    metasession = "%s/%s_%s" % (os.environ['HOME'], ".metasession", target)
    if os.path.exists(metasession):
        (localurl,session) =  open(metasession, 'r').read().strip().split()
        plc = xmlrpclib.Server(localurl, verbose=False, allow_none=True)
    else:
        plc = xmlrpclib.Server(url, verbose=False, allow_none=True)
        if password == None: password = getpass()
        auth = {'Username' : username, 
                'AuthMethod' : 'password',
                'AuthString' : password}
        session = plc.GetSession(auth, expires*(60*60*24))
        with open(metasession, 'w') as f: f.write("%s %s\n" % (url,session)) # 'with' auto-closes

    auth = {'AuthMethod' : 'session', 'session' : session}

    class PLC:
        def __init__(self, plc, auth):
            self.plc = plc
            self.auth = auth

        def __getattr__(self, name):
            method = getattr(self.plc, name)
            if method is None:
                raise AssertionError("Method does not exist: %s" % method)
            if not debug_mode or ('Get' in name or 'AuthCheck' in name):
                return lambda *params : method(self.auth, *params)
            else:
                def call(name,*params):
                    print "DEBUG not running: %s(%s)" % (name, params)
                return lambda *params : call(name,*params)

    plc_api = PLC(plc, auth)
    try:
        # make sure the session is working
        plc_api.AuthCheck()
    except:
        # everything worked except the auth check. try again asking for passwd.
        plc_api = get_plc_api(target, url, username, None, expires, debug_mode)

    return plc_api

def usage(parser):
    print """
myops.py <TARGET> <ACTION> [<object>] [args]
    MYOPS CLI uses sessions to avoid storing passwords.
    You choose the session expiration via --expires days.

TARGET:
    When your session is saved it is identified by your given 'target'
    name.  This is a unique string you chose to identify the --url. 
    For example, one might use:
        plc
        vicci
        test
        vini

ACTION:
    Connect to TARGET and perform ACTION. The current actions are:
        enabled   --  Manage site, node, and slice 'enabled' states.
        
        exempt    --  Manage site, node, and slice exemptions from 
                     myops policy actions.

        removeall --  Remove all exemptions at site from site, nodes, slices 
        addall    --  Add exemptions at site to site, nodes, slices 

        freeze    --  Clamp down everything at a site: 
                        disable site, 
                        disable slices,

        release   --  Release everything at a site: 
                        re-enable site, 
                        re-enable slices,
EXAMPLES:
    # setup session and save target name 'plc' for future calls
    myops.py plc --apiurl https://boot.planet-lab.org/PLCAPI/ \\
                --username soltesz@cs.princeton.edu

    # list current exemptions at plc
    myops.py plc exempt

    # to list only one site (nothing will show if no exemption is present)
    myops.py plc exempt princeton

    # add a new exemption to site 'princeton' for a day
    myops.py plc exempt princeton -a

    # add a new exemption to a specific date
    myops.py plc exempt princeton -a --expires 20120131

""" 
    parser.print_help()

def unparse_expire_str(value):
    expires = time.mktime(time.strptime(value, "%Y%m%d")) - time.time()
    return int(expires)

def parse_expire_str(value):
    import optparse
    if value == "0":
        value = "20990101"
    elif len(value) <= 3:
        # days from now
        value = time.strftime("%Y%m%d", time.localtime(time.time()+int(value)*60*60*24))
    elif len(value) != 8 and value[:3] != "201": # 201 == this decade.
        # flip out
        raise optparse.OptionValueError
    return value

class PlcObj(object):
    def __init__(self, name):
        if type(name) == type(""):
            self.name = name
        elif type(name) == type({}):
            if 'login_base' in name:
                self.name = name['login_base']
            elif 'hostname' in name:
                self.name = name['hostname']
            elif 'name' in name:
                self.name = name['name']

        self.kind = None
        if '_' in self.name: 
            kind = 'Slice'
        elif '.' in self.name: 
            kind='Node'
        else: 
            kind='Site'
        self.kind = kind

    def list(self,target,action,*vals):
        if action == "enabled":
            print ("\t%s %s %s" % (sys.argv[0],target,action)) + (" %-20s --disable" % self.name)
        elif action == "exempt":
            print ("\t%s %s %s" % (sys.argv[0],target,action)) + (" %-20s -a --expires %s" % ((self.name,)+ vals))

    def enable(self,api,state):
        if self.kind == 'Slice':
            # change value of existing slice tag, if it exists.
            tl = api.GetSliceTags({'name' : self.name, 'tagname' : 'enabled', 'value' : '0' if state else '1'})
            if len(tl) == 0:
                api.AddSliceTag(self.name, 'enabled', '1' if state else '0')
            else:
                for t in tl: 
                    api.UpdateSliceTag(t['slice_tag_id'], {'value' : '1' if state else '0'})
        elif self.kind == 'Node':
            if state == True: 
                api.UpdateNode(self.name, {'boot_state' : 'boot'})
            else: 
                api.UpdateNode(self.name, {'boot_state' : 'disabled'})
        elif self.kind == 'Site':
            api.UpdateSite(self.name, {'enabled' : state})
            
    def exempt(self,api,expires):
        if expires != None:
            if self.kind == 'Slice': 
                try: api.AddSliceTag(self.name, 'exempt_slice_until', expires)
                except: api.UpdateSliceTag(self.name, expires)
            elif self.kind == 'Node': 
                try: api.AddNodeTag(self.name, 'exempt_node_until', expires)
                except: api.UpdateNodeTag(self.name, expires)
            elif self.kind == 'Site': 
                try: api.AddSiteTag(api.GetSites(self.name, ['site_id'])[0]['site_id'], 'exempt_site_until', expires)
                except: api.UpdateSiteTag(api.GetSiteTags({'login_base' : self.name, 'tagname' : 'exempt_site_until'})[0]['site_tag_id'], expires)
        else:
            # remove
            if self.kind == 'Slice': 
                tag_id_l = api.GetSliceTags({'name' : self.name, 'tagname' : 'exempt_slice_until'}, ['slice_tag_id'])
                if len(tag_id_l) > 0:   
                    tag_id = tag_id_l[0]['slice_tag_id']
                    api.DeleteSliceTag(tag_id)
            elif self.kind == 'Node': 
                tag_id_l = api.GetNodeTags({'hostname' : self.name, 'tagname' : 'exempt_node_until'}, ['node_tag_id'])
                if len(tag_id_l) > 0: 
                    tag_id = tag_id_l[0]['node_tag_id']
                    api.DeleteNodeTag(tag_id)
            elif self.kind == 'Site': 
                tag_id_l = api.GetSiteTags({'login_base' : self.name, 'tagname' : 'exempt_site_until'}, ['site_tag_id'])
                if len(tag_id_l) > 0: 
                    tag_id = tag_id_l[0]['site_tag_id']
                    api.DeleteSiteTag(tag_id)


def main():
    from optparse import OptionParser
    copy = False
    parser = OptionParser()

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False, help="")
    parser.add_option("-v", "--verbose", dest="verbose", default=False, help="")
    parser.add_option("-u", "--apiurl", dest="url", default="https://www.planet-lab.org/PLCAPI/", help="Set PLC URL for action")
    parser.add_option("-U", "--username", dest="username", default=None, help="Login as username")
    parser.add_option("-P", "--password", dest="password", default=None, help="Use provided password; otherwise prompt for password")
    parser.add_option("-e", "--expires", dest="expires", default="1", help="Set expiration date YYYYMMDD; default is 1 day from now.")
    parser.add_option("", "--disable", dest="disable", default=False, action="store_true", help="Disable object.")
    parser.add_option("-r", "--remove", dest="remove", action="store_true", default=False, help="Remove object from exemption" )
    parser.add_option("-l", "--list", dest="list", action="store_true", default=False, help="List objects with command used to generate them")
    parser.add_option("-a", "--add", dest="add", action="store_true", default=False, help="Add exempt object")
    parser.add_option("-S", "--site", dest="login_base", default=None, help="Act on this site")
    parser.add_option("-H", "--host", dest="hostname", default=None, help="Act on this node")
    parser.add_option("-s", "--slice", dest="slicename", default=None, help="Act on this site")

    (opt, args) = parser.parse_args()
    opt.expires = parse_expire_str(opt.expires)

    if len(args) == 0:
        usage(parser)
        sys.exit(1)

    target = args[0]; 
    api = get_plc_api(target, opt.url, opt.username, opt.password, unparse_expire_str(opt.expires), opt.debug)

    action_list = ['enabled', 'exempt', 'removeall', 'addall', 'release', 'freeze']

    for i,action in enumerate(args[1:]):
        if action in action_list:
            if len(args) > i+2 and args[i+2] not in action_list:
                objname = args[i+2]
            else:
                objname = None

        if action == "enabled":

            if not opt.list and not opt.hostname and not opt.slicename and not opt.login_base:
                opt.list = True
            if opt.list:
                print "Listing only *disabled* objects"
                sites = api.GetSites({'peer_id' : None, 'enabled': False})
                nodes = api.GetNodes({'peer_id' : None, 'boot_state' : 'disabled'})
                slices= api.GetSliceTags({'tagname' : 'enabled'})

                for (header,objlist) in [("Sites:",sites), ("Nodes:", nodes), ("Slices:", slices)]:
                    if len(objlist) > 0: print header
                    for t in objlist:
                        o = PlcObj(t)
                        o.list(target, action)

        if action == "exempt":
            if not opt.list and not opt.remove and not opt.add:
                opt.list = True

            if opt.list:
                if objname == None:
                    sites = api.GetSiteTags({'tagname' : 'exempt_site_until'})
                    nodes = api.GetNodeTags({'tagname' : 'exempt_node_until'})
                    slices = api.GetSliceTags({'tagname' : 'exempt_slice_until'})
                else:
                    try: sites = api.GetSiteTags({'login_base': objname, 'tagname' : 'exempt_site_until'})
                    except: sites = []
                    try: nodes = api.GetNodeTags({'hostname' : objname, 'tagname' : 'exempt_node_until'})
                    except: nodes = []
                    try: slices = api.GetSliceTags({'name' : objname, 'tagname' : 'exempt_slice_until'})
                    except: slices = []

                for (header,objlist) in [("Sites:",sites), ("Nodes:", nodes), ("Slices:", slices)]:
                    if len(objlist) > 0: print header
                    for t in objlist:
                        o = PlcObj(t)
                        o.list(target, action, t['value'])

            if opt.remove:
                if objname == None: raise Exception("provide an object name to remove exemption")
                obj = PlcObj(objname)
                obj.exempt(api,None)

            if opt.add:
                if objname == None: raise Exception("provide an object name to add exemption")
                obj = PlcObj(objname)
                obj.exempt(api,opt.expires)

        if action == "freeze":
            if objname == None: raise Exception("Provide a site name to freeze")
            #  disable site, disable slices,
            try:
                slices = api.GetSlices(api.GetSites(objname, ['slice_ids'])[0]['slice_ids'])
            except:
                slices = []
            obj = PlcObj(objname)
            obj.enable(api,False)
            for sl in slices:
                obj = PlcObj(sl['name'])
                obj.enable(api,False)
                
        if action == "release":
            #  enable site, enable slices,
            if objname == None: raise Exception("Provide a site name to release")
            try:
                slices = api.GetSlices(api.GetSites(objname, ['slice_ids'])[0]['slice_ids'])
            except:
                slices = []
            obj = PlcObj(objname)
            obj.enable(api,True)
            for sl in slices:
                obj = PlcObj(sl['name'])
                obj.enable(api,True)

        if action == "removeall":
            #  remove enable site, enable slices,
            if objname == None: raise Exception("Provide a site name to release")
            try:
                slices = api.GetSlices(api.GetSites(objname, ['slice_ids'])[0]['slice_ids'])
            except:
                slices = []
            obj = PlcObj(objname)
            obj.exempt(api,None)
            for sl in slices:
                obj = PlcObj(sl['name'])
                obj.exempt(api,None)

        if action == "addall":
            if objname == None: raise Exception("Provide a site name to release")
            try:
                slices = api.GetSlices(api.GetSites(objname, ['slice_ids'])[0]['slice_ids'])
            except:
                slices = []
            obj = PlcObj(objname)
            obj.exempt(api,opt.expires)
            for sl in slices:
                obj = PlcObj(sl['name'])
                obj.exempt(api,opt.expires)

if __name__ == '__main__':
    main()
