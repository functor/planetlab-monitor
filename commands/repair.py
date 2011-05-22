#!/usr/bin/python

# This script is used to manipulate the operational state of nodes in
# different node groups.  These are basically set operations on nodes via the
# PLC api.
# 
# Take the ng name as an argument....
# optionally, 
#  * get a list of nodes in the given nodegroup.
#  * set some or all in the set to rins.
#  * restart them all.
#  * do something else to them all.
# 

import os
import time
import traceback
import sys
from optparse import OptionParser

from monitor import config
from monitor import parser as parsermodule
from monitor.common import *
from monitor.const import MINUP
from monitor.model import *
from monitor.wrapper import plc
from monitor.wrapper import plccache
from monitor.database.info.model import *
from monitor.database.info.interface import *

from monitor.query import verify,query_to_dict,node_select

def main(hostnames, config):
    # commands:
    i = 1
    node_count = 1
    print "failboot-repair"
    for i,host in enumerate(hostnames):
        try:
            lb = plccache.plcdb_hn2lb[host]
        except:
            print "unknown host in plcdb_hn2lb %s" % host
            email_exception("%s %s" % (i,host))
            continue

        nodeblack = BlacklistRecord.get_by(hostname=host)

        if nodeblack and not nodeblack.expired():
            print "skipping %s due to blacklist.  will expire %s" % (host, nodeblack.willExpire() )
            continue

        sitehist = SiteInterface.get_or_make(loginbase=lb)

        recent_actions = sitehist.getRecentActions(hostname=host)

        nodehist = HistoryNodeRecord.findby_or_create(hostname=host)

        print "%s %s %s" % (i, nodehist.hostname, nodehist.status)

        if nodehist.status == 'failboot' and \
            changed_greaterthan(nodehist.last_changed, 0.25) and \
            ( not found_between(recent_actions, 'bootmanager_restore', 0.5, 0) \
			or config.force ):
                # send down node notice
                # delay 0.5 days before retrying...
                print "send message for host %s bootmanager_restore" % host
                sitehist.runBootManager(host)

        node_count = node_count + 1
        print "time: ", time.strftime('%Y-%m-%d %H:%M:%S')
        sys.stdout.flush()
        session.flush()

    session.flush()
    return


if __name__ == "__main__":
    parser = parsermodule.getParser(['nodesets'])
    parser.set_defaults(rins=False,
                        reboot=False,
                        force=False, 
                        nosetup=False, 
                        verbose=False, 
                        quiet=False,)

    parser.add_option("", "--force", dest="force", action="store_true", 
                        help="Force action regardless of previous actions/logs.")
    parser.add_option("", "--rins", dest="rins", action="store_true", 
                        help="Set the boot_state to 'rins' for all nodes.")
    parser.add_option("", "--reboot", dest="reboot", action="store_true", 
                        help="Actively try to reboot the nodes, keeping a log of actions.")

    parser.add_option("", "--verbose", dest="verbose", action="store_true", 
                        help="Extra debug output messages.")

    parser = parsermodule.getParser(['defaults'], parser)
    config = parsermodule.parse_args(parser)

    fbquery = HistoryNodeRecord.query.all()
    hostnames = [ n.hostname for n in fbquery ]
    
    if config.site:
        # TODO: replace with calls to local db.  the api fails so often that
        #         these calls should be regarded as unreliable.
        l_nodes = plccache.GetNodesBySite(config.site)
        filter_hostnames = [ n['hostname'] for n in l_nodes ]

        hostnames = filter(lambda x: x in filter_hostnames, hostnames)

    if config.node:
        hostnames = [ config.node ] 

    try:
        main(hostnames, config)
        session.flush()
    except KeyboardInterrupt:
        print "Killed by interrupt"
        session.flush()
        sys.exit(0)
    except:
        email_exception()
        print traceback.print_exc();
        print "fail all..."
