#!/usr/bin/python

import sys
import os
import md5
import re
from monitor.util import file as fileutil

purpose_message="""
  This utility is designed to simplify the task of parsing and generating
  statistics for the number of packages on PlanetLab nodes.
"""

def list_to_md5(strlist):
    digest = md5.new()
    for f in strlist:
        digest.update(f)

    return digest.hexdigest()

def pick_some_rpms(pattern, rpmlist):
    l = []
    cpatt = re.compile(pattern)
    for rpm in rpmlist:
        if cpatt.search(rpm):
            l.append(rpm)
    return l

def main():
    global api
    global config

    from optparse import OptionParser
    parser = OptionParser()

    parser.set_defaults( select=None,
                         input=None,
                         frequency=False,
                         package=True,
                        )

    parser.add_option("", "--input", dest="input", 
                        help="the input file")
    parser.add_option("", "--select", dest="select", 
                        help="the pattern to pull out from rpm list")
    parser.add_option("", "--frequency", dest="frequency", action="store_true",
                        help="print the frequency of packages matched by select")
    parser.add_option("", "--disablepackage", dest="package", action="store_false",
                        help="print the frequency of each pl package")
    (config, args) = parser.parse_args()
    if len(sys.argv) == 1 or config.input is None:
        print purpose_message
        parser.print_help()
        sys.exit(1)

    rpmlist = fileutil.getListFromFile(config.input)

    current_packages_old = ['NodeManager-1.8-5.planetlab',
                'NodeUpdate-0.5-4.planetlab', 'codemux-0.1-13.planetlab',
                'fprobe-ulog-1.1.3-0.planetlab', 'ipod-2.2-1.planetlab',
                'iproute-2.6.16-2.planetlab', 'iptables-1.3.8-9.planetlab',
                'kernel-2.6.22.19-vs2.3.0.34.28.planetlab',
                'madwifi-0.9.4-2.6.22.19.3.planetlab', 'monitor-1.0-7.planetlab',
                'monitor-client-3.0-10.planetlab',
                'monitor-runlevelagent-3.0-10.planetlab', 'pl_mom-2.3-1.planetlab',
                'pl_sshd-1.0-11.planetlab', 'pyplnet-4.3-2.planetlab',
                'util-vserver-pl-0.3-16.planetlab',
                'vserver-planetlab-f8-i386-4.2-12.2009.05.27',
                'vserver-systemslices-planetlab-f8-i386-4.2-12.2009.05.27',
                'vsys-0.9-3.planetlab', 'vsys-scripts-0.95-3.planetlab']

    current_packages = ['NodeManager-1.8-12.planetlab.1',
                'NodeUpdate-0.5-4.planetlab', 'codemux-0.1-13.planetlab',
                'fprobe-ulog-1.1.3-0.planetlab', 'ipod-2.2-1.planetlab',
                'iproute-2.6.16-2.planetlab', 'iptables-1.3.8-9.planetlab',
                'kernel-2.6.22.19-vs2.3.0.34.39.planetlab',
                'madwifi-0.9.4-2.6.22.19.3.planetlab', 'monitor-client-3.0-17.planetlab',
                'monitor-runlevelagent-3.0-17.planetlab', 'pl_mom-2.3-1.planetlab',
                'pl_sshd-1.0-11.planetlab', 'pyplnet-4.3-3.planetlab',
                'util-vserver-pl-0.3-17.planetlab',
                'vserver-planetlab-f8-i386-4.2-12.2009.06.23',
                'vserver-systemslices-planetlab-f8-i386-4.2-12.2009.06.23',
                'vsys-0.9-3.planetlab', 'vsys-scripts-0.95-11.planetlab']

    # PL RPMS
    if config.package:
        all_patterns = map(lambda x: ".*" + x + ".*", [ 'NodeManager', 
                'NodeUpdate', 'codemux', 'fprobe', 'ipod',
                'iproute', 'iptables', 'kernel', 'madwifi', 'monitor-client', 
                'monitor-runlevelagent', 'oombailout', 'pl_mom', 
                'pl_sshd', 'pyplnet', 'util-vserver-pl', 'vserver-planetlab-f8-i386', 
                'vserver-systemslices-planetlab-f8-i386', 'vsys-scripts', 'vsys'])
    else:
        all_patterns = [config.select]
    
    for pattern in all_patterns:
        return_sums = {}
        print "%s --------------------" % pattern
        for line in rpmlist:
            line = line.strip()
            fields = line.split(",")
            host = fields[0]
            rpms = fields[2].split()
            rpms.sort()
            rpms = pick_some_rpms(pattern, rpms)
            if len(rpms) != 0:
                sum = list_to_md5(rpms)
                try:
                    return_sums[sum]['hosts'].append(host)
                except:
                    return_sums[sum] = {'hosts' : [], 'diff' : []}
                    return_sums[sum]['hosts'].append(host)

                return_sums[sum]['diff'] = set(rpms) - set(current_packages) 

        if config.frequency:
            #print "Frequency for packages that matched: %s" % pattern
            sum_list = []
            for sum in return_sums:
                sum_list.append((len(return_sums[sum]['hosts']), sum))

            sum_list.sort(lambda a,b: cmp(b[0], a[0]))
            for sum in sum_list:
                print sum[0], sum[1]
                #if len(return_sums[sum[1]]['hosts']) < 5:
                #    print sum[0], sum[1], map(lambda x: x.replace('.planetlab', ''), return_sums[sum[1]]['diff']) #, return_sums[sum[1]]['hosts']
                #else:
                #    print sum[0], sum[1], map(lambda x: x.replace('.planetlab', ''), return_sums[sum[1]]['diff'])
                #print sum[0], sum[1], len(map(lambda x: x.replace('.planetlab', ''), return_sums[sum[1]]['diff']))

if __name__ == "__main__":
    try:
        main()
    except IOError:
        pass
