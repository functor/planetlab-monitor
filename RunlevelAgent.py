#!/usr/bin/python

import xml, xmlrpclib
import logging
import time
import traceback
import sys
import os
import string

CONFIG_FILE="/tmp/source/configuration"
SESSION_FILE="/etc/planetlab/session"

def read_config_file(filename):
    ## NOTE: text copied from BootManager.py 
    # TODO: unify this code to make it common. i.e. use ConfigParser module
    vars = {}
    vars_file= file(filename,'r')
    validConfFile = True
    for line in vars_file:
        # if its a comment or a whitespace line, ignore
        if line[:1] == "#" or string.strip(line) == "":
            continue

        parts= string.split(line,"=")
        if len(parts) != 2:
            print "Invalid line in vars file: %s" % line
            validConfFile = False
            break

        name= string.strip(parts[0])
        value= string.strip(parts[1])
        vars[name]= value

    vars_file.close()
    if not validConfFile:
        print "Unable to read configuration vars."

    return vars

try:
    sys.path = ['/etc/planetlab'] + sys.path
    import plc_config
    api_server_url = "https://" + plc_config.PLC_API_HOST + plc_config.PLC_API_PATH
except:
    filename=CONFIG_FILE
    vars = read_config_file(filename)
    api_server_url = vars['BOOT_API_SERVER']


class Auth:
    def __init__(self, username=None, password=None, **kwargs):
        if 'session' in kwargs:
            self.auth= { 'AuthMethod' : 'session',
                    'session' : kwargs['session'] }
        else:
            if username==None and password==None:
                self.auth = {'AuthMethod': "anonymous"}
            else:
                self.auth = {'Username' : username,
                            'AuthMethod' : 'password',
                            'AuthString' : password}
class PLC:
    def __init__(self, auth, url):
        self.auth = auth
        self.url = url
        self.api = xmlrpclib.Server(self.url, verbose=False, allow_none=True)

    def __getattr__(self, name):
        method = getattr(self.api, name)
        if method is None:
            raise AssertionError("method does not exist")

        return lambda *params : method(self.auth.auth, *params)

    def __repr__(self):
        return self.api.__repr__()

def main():

    f=open(SESSION_FILE,'r')
    session_str=f.read().strip()
    api = PLC(Auth(session=session_str), api_server_url)
    # NOTE: should we rely on bootmanager for this functionality?
    api.AuthCheck()

    try:
        env = 'production'
        if len(sys.argv) > 1:
            env = sys.argv[1]
    except:
        traceback.print_exc()
        pass

    while True:
        # TODO: remove from output
        print "reporting status: ", os.popen("uptime").read().strip()
        try:
            # NOTE: alternately, check other stuff in the environment to infer
            # run_level
            #     is BootManager running?
            #     what is the boot_state at PLC?
            #     does /vservers exist?
            #     what about /tmp/source?
            #     is BootManager in /tmp/source?
            #     is /tmp/mnt/sysimg mounted?
            #     how long have we been running?  if we were in safeboot and
            #       still running, we're likely in failboot now.
            #     length of runtime increases the certainty of inferred state.
            #     
            if env == "bootmanager":
                # if bm not running, and plc bootstate = boot, then
                api.ReportRunlevel({'run_level' : 'failboot'})
                api.ReportRunlevel({'run_level' : 'reinstall'})
                # if bm not running, and plc bootstate = safeboot, then
                api.ReportRunlevel({'run_level' : 'safeboot'})
            elif env == "production":
                api.ReportRunlevel({'run_level' : 'boot'})
            else:
                api.ReportRunlevel({'run_level' : 'failboot'})
                
        except:
            traceback.print_exc()

        # TODO: change to a configurable value
        sys.stdout.flush()
        time.sleep(60)

if __name__ == "__main__":
    main()
