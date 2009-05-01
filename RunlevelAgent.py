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

def extract_from(filename, pattern):
    f = os.popen("grep -E %s %s" % (pattern, filename))
    val = f.read().strip()
    return val

def check_running(commandname):
    f = os.popen("ps ax | grep -E %s | grep -v grep" % (commandname))
    val = f.read().strip()
    return val
    

def main():

    f=open(SESSION_FILE,'r')
    session_str=f.read().strip()
    api = PLC(Auth(session=session_str), api_server_url)
    # NOTE: What should we do if this call fails?
    api.AuthCheck()

    try:
        env = 'production'
        if len(sys.argv) > 1:
            env = sys.argv[1]
    except:
        traceback.print_exc()

    while True:
        try:
            # NOTE: here we are inferring the runlevel by environmental
            #         observations.  We know how this process was started by the
            #         given command line argument.  Then in bootmanager
            #         runlevle, the bm.log gives information about the current
            #         activity.
            # other options:
            #   call plc for current boot state?
            #   how long have we been running?
            if env == "bootmanager":
                bs_val = extract_from('/tmp/bm.log', 'Current boot state:')
                if len(bs_val) > 0: bs_val = bs_val.split()[-1]
                ex_val = extract_from('/tmp/bm.log', 'Exception')
                fs_val = extract_from('/tmp/bm.log', 'mke2fs')
                bm_val = check_running("BootManager.py")

                if bs_val in ['diag', 'diagnose', 'safeboot', 'disabled', 'disable']:
                    api.ReportRunlevel({'run_level' : 'safeboot'})

                elif len(ex_val) > len("Exception"):
                    api.ReportRunlevel({'run_level' : 'failboot'})

                elif len(fs_val) > 0 and len(bm_val) > 0:
                    api.ReportRunlevel({'run_level' : 'reinstall'})

                else:
                    api.ReportRunlevel({'run_level' : 'failboot'})

            elif env == "production":
                api.ReportRunlevel({'run_level' : 'boot'})
            else:
                api.ReportRunlevel({'run_level' : 'failboot'})
                
        except:
            print "reporting error: ", os.popen("uptime").read().strip()
            traceback.print_exc()

        sys.stdout.flush()
        # TODO: change to a configurable value
        time.sleep(60*15)

if __name__ == "__main__":
    main()
