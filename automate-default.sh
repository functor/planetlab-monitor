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


echo "Performing Findbad Nodes"
#########################
# 1. FINDBAD NODES 
rm -f ${MONITOR_DATA_ROOT}/production.findbad2.pkl
${MONITOR_SCRIPT_ROOT}/findbad.py --increment --cachenodes --debug=0 --dbname="findbad2" $DATE || :
cp ${MONITOR_DATA_ROOT}/production.findbad2.pkl ${MONITOR_DATA_ROOT}/production.findbad.pkl
ps ax | grep BatchMode | grep -v grep | awk '{print $1}' | xargs -r kill || :

echo "Performing Findbad PCUs"
#########################
# 2. FINDBAD PCUS
rm -f ${MONITOR_DATA_ROOT}/production.findbadpcus2.pkl
${MONITOR_SCRIPT_ROOT}/findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus2 $DATE || :
cp ${MONITOR_DATA_ROOT}/production.findbadpcus2.pkl ${MONITOR_DATA_ROOT}/production.findbadpcus.pkl
# clean up stray 'locfg' processes that hang around inappropriately...
ps ax | grep locfg | grep -v grep | awk '{print $1}' | xargs -r kill || :

#echo "Generating web data"
# badcsv.txt
#${MONITOR_SCRIPT_ROOT}/printbadcsv.py  | grep -v loading | tr -d ' ' > badcsv.txt
#cp badcsv.txt /plc/data/var/www/html/monitor/
#${MONITOR_SCRIPT_ROOT}/showlatlon.py | head -9 | awk 'BEGIN {print "<table>"} { print "<tr><td>", $0, "</td></tr>"} END{print "</table>"}'  | sed -e 's\|\</td><td>\g' > /plc/data/var/www/html/monitor/regions.html

echo "Performing uptime changes for sites, nodes, and pcus"
########################
# 3. record last-changed for sites, nodes and pcus.
${MONITOR_SCRIPT_ROOT}/sitebad.py --increment || :
${MONITOR_SCRIPT_ROOT}/nodebad.py --increment || :
${MONITOR_SCRIPT_ROOT}/pcubad.py --increment || :

echo "Converting pkl files to phpserial"
#########################
# 4. convert pkl to php serialize format.
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i findbadpcus2 -o findbadpcus
for f in act_all plcdb_hn2lb ; do
	if [ -f ${MONITOR_DATA_ROOT}/production.$f.pkl ]; then
		${MONITOR_SCRIPT_ROOT}/pkl2php.py -i $f -o $f
	else
		echo "Warning: ${MONITOR_DATA_ROOT}/production.$f.pkl does not exist."
	fi
done
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i findbad -o findbadnodes
#${MONITOR_SCRIPT_ROOT}/pkl2php.py -i ad_dbTickets -o ad_dbTickets
#${MONITOR_SCRIPT_ROOT}/pkl2php.py -i idTickets -o idTickets

echo "Archiving pkl files"
#########################
# Archive pkl files.
for f in findbad act_all findbadpcus l_plcnodes site_persistflags node_persistflags pcu_persistflags ; do
	if [ -f ${MONITOR_DATA_ROOT}/production.$f.pkl ] ; then
		cp ${MONITOR_DATA_ROOT}/production.$f.pkl ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.production.$f.pkl
	else
		echo "Warning: It failed to archive ${MONITOR_DATA_ROOT}/production.$f.pkl"
	fi
done

echo "Running grouprins on all dbg nodes"
############################
# 5. Check if there are any nodes in dbg state.  Clean up afterward.
${MONITOR_SCRIPT_ROOT}/grouprins.py --mail=1 --reboot --nodeselect 'state=DOWN&&boot_state=(boot|rins|dbg|diag)' --stopselect "state=BOOT" || :
${MONITOR_SCRIPT_ROOT}/grouprins.py --mail=1 --reboot --nodeselect 'state=DEBUG&&boot_state=(rins|dbg|boot)' --stopselect 'state=BOOT' || :

cp ${MONITOR_SCRIPT_ROOT}/monitor.log ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.monitor.log
rm -f $MONITOR_PID
