#!/bin/bash

# NOTE: Must be an absolute path to guarantee it is read.
source /usr/share/monitor-server/monitorconfig.py
cd ${MONITOR_SCRIPT_ROOT}
set -e
DATE=`date +%Y-%m-%d-%T`
MONITOR_PID="$HOME/monitor/SKIP"

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
		${MONITOR_SCRIPT_ROOT}/kill.cmd.sh $PID
	else 
		# skipping monitor
		echo "SKIPPING Monitor"
		exit
	fi 
fi
echo $$ > $MONITOR_PID

AGENT=`ps ax | grep ssh-agent | grep -v grep`
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
ps ax | grep BatchMode | grep -v grep | awk '{print $1}' | xargs kill || :

echo "Performing Findbad PCUs"
#########################
# 2. FINDBAD PCUS
rm -f ${MONITOR_DATA_ROOT}/production.findbadpcus2.pkl
${MONITOR_SCRIPT_ROOT}/findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus2 $DATE || :
cp ${MONITOR_DATA_ROOT}/production.findbadpcus2.pkl ${MONITOR_DATA_ROOT}/production.findbadpcus.pkl
# clean up stray 'locfg' processes that hang around inappropriately...
ps ax | grep locfg | grep -v grep | awk '{print $1}' | xargs kill || :

echo "Generating web data"
# badcsv.txt
${MONITOR_SCRIPT_ROOT}/printbadcsv.py  | grep -v loading | tr -d ' ' > badcsv.txt
cp badcsv.txt /plc/data/var/www/html/monitor/
${MONITOR_SCRIPT_ROOT}/showlatlon.py | head -9 | awk 'BEGIN {print "<table>"} { print "<tr><td>", $0, "</td></tr>"} END{print "</table>"}'  | sed -e 's\|\</td><td>\g' > /plc/data/var/www/html/monitor/regions.html

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
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i act_all -o act_all
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i plcdb_hn2lb -o plcdb_hn2lb
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i findbad -o findbadnodes
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i ad_dbTickets -o ad_dbTickets
${MONITOR_SCRIPT_ROOT}/pkl2php.py -i idTickets -o idTickets

echo "Archiving pkl files"
#########################
# Archive pkl files.
for f in findbad act_all findbadpcus l_plcnodes site_persistflags node_persistflags pcu_persistflags ; do 
	cp ${MONITOR_DATA_ROOT}/production.$f.pkl ${MONITOR_ARCHIVE_ROOT}/`date +%F-%H:%M`.production.$f.pkl
done

echo "Running grouprins on all dbg nodes"
############################
# 5. Check if there are any nodes in dbg state.  Clean up afterward.
${MONITOR_SCRIPT_ROOT}/grouprins.py --mail=1 \
	--nodeselect 'state=DEBUG&&boot_state=(rins|dbg|boot)' \
	--stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.9.planetlab' \
	--reboot || :
${MONITOR_SCRIPT_ROOT}/findbad.py --increment --cachenodes --debug=0 --dbname="findbad" --nodeselect 'state=DEBUG&&boot_state=dbg||state=DEBUG&&boot_state=boot' || :

echo "Collecting RT database dump"
##########################
# 6. cache the RT db locally.
python ${MONITOR_SCRIPT_ROOT}/rt.py

rm -f $MONITOR_PID
