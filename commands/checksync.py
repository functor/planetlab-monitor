#!/usr/bin/python

from monitor.database.info.model import *
import sys

fbquery = HistoryNodeRecord.query.all()
hostnames = [ n.hostname for n in fbquery ]

if True:
	for hn in hostnames:
		fbrec = FindbadNodeRecord.query.filter_by(hostname=hn).order_by(FindbadNodeRecord.version.desc()).first()
		if len(fbrec.versions) >= 2:
			if fbrec.version != fbrec.versions[-2].version + 1:
				print fbrec.hostname, fbrec.version, fbrec.versions[-2].version
				fbrec.version = fbrec.versions[-2].version + 1
				fbrec.flush()

	session.flush()

fbquery = HistoryPCURecord.query.all()
pcus = [ n.plc_pcuid for n in fbquery ]

for pcuid in pcus:
	fbrec = FindbadPCURecord.query.filter_by(plc_pcuid=pcuid).order_by(FindbadPCURecord.version.desc()).first()
	if len(fbrec.versions) >= 2:
		if fbrec.version != fbrec.versions[-2].version + 1:
			print fbrec.plc_pcuid, fbrec.version, fbrec.versions[-2].version
			fbrec.version = fbrec.versions[-2].version + 1
			fbrec.flush()

session.flush()
