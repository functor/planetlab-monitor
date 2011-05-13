#!/usr/bin/python

import csv
import sys
import os
from glob import glob

import vxargs
from monitor import parser as parsermodule
from monitor import common
from automate import *

def build_vx_args_external(shell_cmd):
    args = shell_cmd.split()
    return args

def vx_start_external(filelist,outdir,cmd, timeout=0, threadcount=20):
    args = build_vx_args_external(cmd)
    vxargs.start(None, threadcount, filelist, outdir, False, args, timeout)

def build_vx_args(shell_cmd):
    ssh_options="-q -o UserKnownHostsFile=junkssh -o StrictHostKeyChecking=no"
    cmd="""ssh %s root@{} """  % ssh_options
    args = cmd.split()
    args.append(shell_cmd)
    return args

def vx_start(filelist,outdir,cmd, timeout=0):
    args = build_vx_args(cmd)
    vxargs.start(None, 20, filelist, outdir, False, args, timeout)

def get_hostlist_from_myops(filter):
    ret = []
    curl_url = "curl -s 'http://myops.planet-lab.org:5984/query"
    curl_params = "fields=hostname&skip_header&filter=%s'" % filter
    curl_cmd = "%s?%s" % (curl_url, curl_params)
    print curl_cmd
    f = os.popen(curl_cmd, 'r')
    for h in f.read().split():
        ret.append((h, ''))
    return ret

if __name__ == "__main__":

    parser = parsermodule.getParser(['nodesets'])
    parser.set_defaults(outdir=None,
                        timeout=0,
                        simple=False,
                        threadcount=20,
                        external=False,
                        myopsfilter=None,
                        run=False,
                        template=None,
                        cmdfile=None,)

    parser.add_option("", "--timeout", dest="timeout", metavar="seconds",
                        help="Number of seconds to wait before timing out on host.")
    parser.add_option("", "--myopsfilter", dest="myopsfilter", metavar="",
                        help="filter string to pass directly to myops query")
    parser.add_option("", "--outdir", dest="outdir", metavar="dirname",
                        help="Name of directory to place output")
    parser.add_option("", "--cmd", dest="cmdfile", metavar="filename",
                        help="Name of file that contains a unix-to-csv command " + \
                             "to run on the hosts.")
    parser.add_option("", "--external", dest="external",  action="store_true",
                        help="Run commands external to the server. The default is internal.")
    parser.add_option("", "--template", dest="template", 
                        help="Command template for external commands; substitutes {} with hostname.")
    parser.add_option("", "--threadcount", dest="threadcount", 
                        help="Number of simultaneous threads: default 20.")

    config = parsermodule.parse_args(parser)

    if config.outdir == None: 
        outdir="checkhosts"
    else: 
        outdir=config.outdir

    if not os.path.exists(outdir):
        os.system('mkdir -p %s' % outdir)

    #if config.site is not None or \
    #   config.nodeselect is not None or \
    #   config.nodegroup is not None:
    #    print "TODO: implement support for nodeselect and site queries."
    #    print "%s %s %s" % (config.site, config.nodeselect, config.nodegroup)
    #    sys.exit(1)
    if config.myopsfilter is not None:
        filelist = get_hostlist_from_myops(config.myopsfilter)
    else:
        nodelist = common.get_nodeset(config)
        if len(nodelist) > 0:
            filelist = [ (x, '') for x in nodelist ]
        elif os.path.exists(str(config.nodelist)) and os.path.isfile(config.nodelist):
            filelist = vxargs.getListFromFile(open(config.nodelist,'r'))
        elif os.path.exists(str(config.nodelist)) and os.path.isdir(config.nodelist):
            filelist = get_hostlist_from_dir(config.nodelist)
        elif config.node is not None:
            filelist = [(config.node, '')]
        else:
            # probably no such file.
            raise Exception("No such file %s" % config.nodelist)

    if config.cmdfile == None and config.template == None:
        f = open("command.txt",'r')
        cmd = f.read()
    elif config.template is not None and config.external:
        cmd = config.template
    else:
        f = open(config.cmdfile,'r')
        cmd = f.read()

    print filelist

    if config.external or config.template is not None:
        vx_start_external(filelist, outdir, cmd, int(config.timeout), int(config.threadcount))
    else:
        vx_start(filelist, outdir, cmd, int(config.timeout))
        
