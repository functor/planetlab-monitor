#!/bin/bash

export PATH=$PATH:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# NOTE: Must be an absolute path to guarantee it is read.
INSTALLPATH=/usr/share/monitor/
$INSTALLPATH/commands/shconfig.py >  $INSTALLPATH/monitorconfig.sh
source $INSTALLPATH/monitorconfig.sh
cd ${MONITOR_SCRIPT_ROOT}
set -e
DATE=`date +%Y-%m-%d-%T`
MONITOR_PID="${MONITOR_SCRIPT_ROOT}/SKIP"

function send_mail ()
{
    subject=$1
    body=$2
    mail -s "$subject" $exception_email <<EOF
$body
EOF
}


echo "#######################################"; echo "Running Monitor at $DATE"; echo "######################################"
echo "Performing API test"
API=$(${MONITOR_SCRIPT_ROOT}/tools/testapi.py)
if [ "$API" != "ok" ] ; then 
	# NOTE: Do not try to run any commands if the API is obviously broken.
	echo "API IS DOWN : "`date`
	exit 1
fi

if [ -f $MONITOR_PID ] ; then 
	if [ -z "$1" ] ; then 
		echo "KILLING Monitor"
		PID=`cat $MONITOR_PID`
		rm -f $MONITOR_PID
		if [ -z $PID ] ; then
			${MONITOR_SCRIPT_ROOT}/tools/kill.cmd.sh $PID
			echo "done."
		else
			echo "No PID to be killed."
		fi
	else 
		# skipping monitor
		echo "SKIPPING Monitor"
		exit
	fi 
fi
echo $$ > $MONITOR_PID

# SETUP act_all database if it's not there.
if [ ! -f ${MONITOR_SCRIPT_ROOT}/actallsetup.flag ]; then
	if ! python -c 'import database; database.dbLoad("act_all")' 2>/dev/null ; then 
		touch ${MONITOR_SCRIPT_ROOT}/actallsetup.flag
	fi
fi


set +e
AGENT=`ps ax | grep ssh-agent | grep -v grep`
set -e
if [ -z "$AGENT" ] ; then
        echo "starting ssh agent"
        # if no agent is running, set it up.
        ssh-agent > ${MONITOR_SCRIPT_ROOT}/agent.sh
        source ${MONITOR_SCRIPT_ROOT}/agent.sh
        ssh-add /etc/planetlab/myops_ssh_key.rsa
        ssh-add /etc/planetlab/debug_ssh_key.rsa
        ssh-add /etc/planetlab/root_ssh_key.rsa
fi
#TODO: should add a call to ssh-add -l to check if the keys are loaded or not.
source ${MONITOR_SCRIPT_ROOT}/agent.sh

# CHECK AGENT IS UP AND RUNNING
count=$( ssh-add -l | wc -l ) 
if [ $count -lt 3 ] ; then
    send_mail "ssh-agent is not up and running." "Add keys before monitoring can continue"
	exit
fi

${MONITOR_SCRIPT_ROOT}/commands/syncwithplc.py $DATE || :
service plc restart monitor

echo "Performing FindAll Nodes"
#########################
# 1. FINDBAD NODES 
${MONITOR_SCRIPT_ROOT}/commands/findall.py $DATE || :
ps ax | grep BatchMode | grep -v grep | awk '{print $1}' | xargs -r kill || :
# clean up stray 'locfg' processes that hang around inappropriately...
ps ax | grep locfg | grep -v grep | awk '{print $1}' | xargs -r kill || :


${MONITOR_SCRIPT_ROOT}/commands/policy.py $DATE || :
curl -s 'http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeview&formatcsv' > /var/lib/monitor/comon/$DATE.comon.csv || :

cp ${MONITOR_SCRIPT_ROOT}/monitor.log ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.monitor.log
service plc restart monitor || :
rm -f $MONITOR_PID
