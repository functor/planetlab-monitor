#!/bin/bash

# NOTE: Must be an absolute path to guarantee it is read.
INSTALLPATH=/usr/share/monitor/
# Generate an 'sh' style file full of variables in monitor.conf
$INSTALLPATH/shconfig.py >  $INSTALLPATH/monitorconfig.sh
source $INSTALLPATH/monitorconfig.sh
cd ${MONITOR_SCRIPT_ROOT}
set -e
DATE=`date +%Y-%m-%d-%T`
MONITOR_PID="${MONITOR_SCRIPT_ROOT}/SKIP"

echo "#######################################"; echo "Running Monitor at $DATE"; echo "######################################"
echo "Performing API test"
API=$(./testapi.py)
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
			${MONITOR_SCRIPT_ROOT}/kill.cmd.sh $PID
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
        ssh-add /etc/planetlab/debug_ssh_key.rsa
        ssh-add /etc/planetlab/root_ssh_key.rsa
fi
#TODO: should add a call to ssh-add -l to check if the keys are loaded or not.
source ${MONITOR_SCRIPT_ROOT}/agent.sh


echo "Performing FindAll Nodes"
#########################
# 1. FINDBAD NODES 
${MONITOR_SCRIPT_ROOT}/findall.py --increment $DATE || :
ps ax | grep BatchMode | grep -v grep | awk '{print $1}' | xargs -r kill || :
# clean up stray 'locfg' processes that hang around inappropriately...
ps ax | grep locfg | grep -v grep | awk '{print $1}' | xargs -r kill || :

${MONITOR_SCRIPT_ROOT}/policy.py $DATE

echo "Archiving pkl files"
#########################
# Archive pkl files.
for f in act_all l_plcnodes site_persistflags node_persistflags pcu_persistflags ; do
	if [ -f ${MONITOR_DATA_ROOT}/production.$f.pkl ] ; then
		cp ${MONITOR_DATA_ROOT}/production.$f.pkl ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.production.$f.pkl
	else
		echo "Warning: It failed to archive ${MONITOR_DATA_ROOT}/production.$f.pkl"
	fi
done

############################
# 5. Check if there are any nodes in dbg state.  Clean up afterward.
#${MONITOR_SCRIPT_ROOT}/grouprins.py --mail=1 --reboot --nodeselect 'state=DOWN&&boot_state=(boot|rins|dbg|diag)' --stopselect "state=BOOT" || :
#${MONITOR_SCRIPT_ROOT}/grouprins.py --mail=1 --reboot --nodeselect 'state=DEBUG&&boot_state=(rins|dbg|boot)' --stopselect 'state=BOOT' || :

cp ${MONITOR_SCRIPT_ROOT}/monitor.log ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.monitor.log
rm -f $MONITOR_PID
