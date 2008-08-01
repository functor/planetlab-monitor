#!/bin/bash

set -e
cd $HOME/monitor/
DATE=`date +%Y-%m-%d-%T`

if [ -f $HOME/monitor/SKIP ] ; then 
	#	echo "SKIPPING Monitor"
	#	exit
	# TODO: should be possible to kill the old version if 
	# desired and prevent lingering instances of automate.
	if [ -z "$1" ] ; then 
		echo "KILLING Monitor"
		PID=`cat $HOME/monitor/SKIP`
		rm -f $HOME/monitor/SKIP
		./kill.cmd.sh $PID
	else 
		# skipping monitor
		echo "SKIPPING Monitor"
		exit
	fi 
fi
echo $$ > $HOME/monitor/SKIP

#########################
# 1. FINDBAD NODES 
rm -f pdb/production.findbad2.pkl
./findbad.py --increment --cachenodes --debug=0 --dbname="findbad2" $DATE || :

ps ax | grep BatchMode | grep -v grep | awk '{print $1}' | xargs kill || :

########################
# COPY to golf for diagnose.py and action.py
cp pdb/production.findbad2.pkl pdb/production.findbad.pkl
#scp pdb/production.findbad2.pkl soltesz@golf.cs.princeton.edu:monitor3/pdb/production.findbad.pkl

########################
# COPY Act_all records
#scp soltesz@golf.cs.princeton.edu:monitor3/pdb/production.act_all.pkl pdb/

########################
# badcsv.txt
./printbadcsv.py  | grep -v loading | tr -d ' ' > badcsv.txt
cp badcsv.txt /plc/data/var/www/html/monitor/
./showlatlon.py | head -9 | awk 'BEGIN {print "<table>"} { print "<tr><td>", $0, "</td></tr>"} END{print "</table>"}'  | sed -e 's\|\</td><td>\g' > /plc/data/var/www/html/monitor/regions.html

#########################
# 2. FINDBAD PCUS
rm -f pdb/production.findbadpcus2.pkl
./findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus2 $DATE || :

./sitebad.py --increment || :
./nodebad.py --increment || :
./pcubad.py --increment || :

# clean up stray 'locfg' processes that hang around inappropriately...
ps ax | grep locfg | grep -v grep | awk '{print $1}' | xargs kill || :

# convert pkl to php serialize format.
cp pdb/production.findbadpcus2.pkl pdb/production.findbadpcus.pkl

./pkl2php.py -i findbadpcus2 -o findbadpcus
./pkl2php.py -i act_all -o act_all
./pkl2php.py -i plcdb_hn2lb -o plcdb_hn2lb
./pkl2php.py -i findbad -o findbadnodes
./pkl2php.py -i ad_dbTickets -o ad_dbTickets
./pkl2php.py -i idTickets -o idTickets

#for f in findbad act_all findbadpcus l_plcnodes; do 
#for f in findbad act_all findbadpcus l_plcnodes site_persistflags ; do 
for f in findbad act_all findbadpcus l_plcnodes site_persistflags node_persistflags pcu_persistflags ; do 
	cp pdb/production.$f.pkl archive-pdb/`date +%F-%H:%M`.production.$f.pkl
done

./grouprins.py --mail=1 \
	--nodeselect 'state=DEBUG&&boot_state=dbg||state=DEBUG&&boot_state=boot' \
	--stopselect 'state=BOOT&&kernel=2.6.22.19-vs2.3.0.34.9.planetlab' \
	--reboot || :

# cache the RT db locally.
python ./rt.py

rm -f $HOME/monitor/SKIP
