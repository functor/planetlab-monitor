#!/bin/bash

set -e
cd $HOME/monitor/

#########################
# 1. FINDBAD NODES 
rm -f pdb/production.findbad2.pkl
./findbad.py --cachenodes --debug=0 --dbname="findbad2"

########################
# COPY to golf for diagnose.py and action.py
cp pdb/production.findbad2.pkl pdb/production.findbad.pkl
scp pdb/production.findbad2.pkl soltesz@golf.cs.princeton.edu:monitor3/pdb/production.findbad.pkl

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
./findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus2
# convert pkl to php serialize format.
cp pdb/production.findbadpcus2.pkl pdb/production.findbadpcus.pkl
./pkl2php.py -i findbadpcus2 -o findbadpcus


for f in findbad act_all findbadpcus l_plcnodes; do 
	cp pdb/production.$f.pkl archive-pdb/`date +%F`.production.$f.pkl
done
