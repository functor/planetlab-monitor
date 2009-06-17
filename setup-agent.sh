#!/bin/bash

# NOTE: Must be an absolute path to guarantee it is read.
INSTALLPATH=/usr/share/monitor/
# Generate an 'sh' style file full of variables in monitor.conf
$INSTALLPATH/shconfig.py >  $INSTALLPATH/monitorconfig.sh
source $INSTALLPATH/monitorconfig.sh
cd ${MONITOR_SCRIPT_ROOT}
set -e
DATE=`date +%Y-%m-%d-%T`

set +e
AGENT=`ps ax | grep ssh-agent | grep -v grep`
set -e
if [ -z "$AGENT" ] ; then
        echo "starting ssh agent"
        # if no agent is running, set it up.
        ssh-agent > ${MONITOR_SCRIPT_ROOT}/agent.sh
        source ${MONITOR_SCRIPT_ROOT}/agent.sh
        ssh-add /etc/planetlab/debug_ssh_key.rsa
        ssh-add /etc/planetlab/root_ssh_key.rsa
fi
#TODO: should add a call to ssh-add -l to check if the keys are loaded or not.
source ${MONITOR_SCRIPT_ROOT}/agent.sh
exit

