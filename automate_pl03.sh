#!/bin/bash

set -e
cd $HOME/monitor/
DATE=`date +%Y-%m-%d-%T`

#########################
# 1. FINDBAD NODES 
rm -f pdb/production.findbad2.pkl
./findbad.py --cachenodes --debug=0 --dbname="findbad2" $DATE

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

#########################
# 2. FINDBAD PCUS
rm -f pdb/production.findbadpcus2.pkl
./findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus2 $DATE		
# convert pkl to php serialize format.
cp pdb/production.findbadpcus2.pkl pdb/production.findbadpcus.pkl
./pkl2php.py -i findbadpcus2 -o findbadpcus

./pkl2php.py -i act_all -o act_all
./pkl2php.py -i plcdb_hn2lb -o plcdb_hn2lb
./pkl2php.py -i findbad -o findbadnodes
./pkl2php.py -i ad_dbTickets -o ad_dbTickets
./pkl2php.py -i idTickets -o idTickets

for f in findbad act_all findbadpcus l_plcnodes; do 
	cp pdb/production.$f.pkl archive-pdb/`date +%F`.production.$f.pkl
done
