#!/bin/bash

set -e
cd $HOME/research/planetlab/svn/monitor/
source ssh.env.sh
export SSH_AUTH_SOCK
rm -f pdb/production.findbad2.pkl
./findbad.py --cachenodes --debug=0 --dbname="findbad2"
# rename, and copies to golf.
cp  pdb/production.findbad2.pkl pdb/production.findbad.pkl
scp pdb/production.findbad2.pkl soltesz@golf.cs.princeton.edu:monitor3/pdb/production.findbad.pkl
scp soltesz@golf.cs.princeton.edu:monitor3/pdb/production.act_all.pkl ~/public_html/cgi-bin/pdb/debug.act_all.pkl
# make available for local cgi-bin scripts
cp pdb/production.findbad2.pkl ~/public_html/cgi-bin/pdb/debug.findbad.pkl
# generate badcsv for tux/public_html scripts.
./printbadcsv.py  | grep -v loading | tr -d ' ' > badcsv.txt
scp badcsv.txt soltesz@tux.cs.princeton.edu:public_html/


ssh soltesz@pl-virtual-03 "cd monitor3; ./findbadpcu.py --increment --refresh --debug=0 --dbname=findbadpcus"
scp soltesz@pl-virtual-03:monitor3/pdb/production.findbadpcus.phpserial pdb/
