#!/usr/bin/python
from monitor.database.info.model import *

def getSequences():

		# TODO: This can be replaced with a DB definition at a future time.
		# 		This would make it possible for an admin to introduce new
		# 		patterns without touching code.
		
		sequences = {}
		# restart_bootmanager_boot
		for n in ["bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-protoerror-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-implementerror-bootupdatefail-update-debug-done",

				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-exception-protoerror-update-protoerror-debug-done",

				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-exception-protoerror-protoerror2-protoerror-protoerror2-debug-validate-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-exception-protoerror-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-exception-protoerror-protoerror-debug-validate-done",
				"bminit-cfg-auth-protoerror-exception-update-debug-validate-exception-done",
				"bminit-cfg-auth-getplc-update-debug-done",
				"bminit-cfg-auth-protoerror2-debug-done",
				"bminit-cfg-auth-getplc-exception-protoerror-update-protoerror-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-protoerror-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-bootupdatefail-authfail-debug-done",
				"bminit-cfg-auth-protoerror-exception-update-debug-done",
				"bminit-cfg-auth-getplc-exception-protoerror-update-debug-done",
				"bminit-cfg-auth-getplc-implementerror-update-debug-done",
				"bminit-cfg-auth-authfail2-protoerror2-debug-done",
				]:
			sequences.update({n : "restart_bootmanager_boot"})

		#	conn.restart_bootmanager('reinstall')
		for n in [ "bminit-cfg-auth-getplc-installinit-validate-exception-modulefail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-modulefail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-bziperror-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-exception-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nofilereference-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-exception-mkfsfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-installcfg-installstop-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-kernelcopyfail-exception-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-installcfg-installstop-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-kernelcopyfail-exception-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-exception-noinstall-update-debug-done",
				# actual solution appears to involve removing the bad files, and
				# continually trying to boot the node.
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-implementerror-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-exception-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-bmexceptmount-exception-noinstall-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-noinstall-update-debug-validate-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptvgscan-exception-noinstall-update-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-installinit-validate-bmexceptvgscan-exception-noinstall-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-bmexceptvgscan-exception-noinstall-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-exception-missingkernel-debug-validate-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-implementerror-nospace-debug-validate-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-disk-update4-update3-update3-nospace-nospace-nospace-nospace-nospace-nospace-nospace-nospace-implementerror-nospace-debug-validate-done",
				]:
			sequences.update({n : "restart_bootmanager_rins"})

		# repair_node_keys
		for n in ["bminit-cfg-auth-bootcheckfail-authfail-exception-update-bootupdatefail-authfail-debug-validate-exception-done",
					"bminit-cfg-auth-bootcheckfail-authfail-exception-update-bootupdatefail-authfail-debug-done",
					"bminit-cfg-auth-bootcheckfail-authfail-exception-update-debug-validate-exception-done",
					"bminit-cfg-auth-bootcheckfail-authfail-exception-authfail-debug-validate-exception-done",
					"bminit-cfg-auth-authfail-debug-done",
					"bminit-cfg-auth-authfail2-authfail-debug-done",
				]:
			sequences.update({n: "repair_node_keys"})

		#   conn.restart_node('reinstall')
		for n in ["bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-installcfg-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-writeerror-exception-chrootfail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-exception-bmexceptrmfail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-installinit-exception-bmexceptrmfail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-disk-update4-update3-implementerror-bootupdatefail-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-readonlyfs-update-debug-done",
				"bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-nospace-exception-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nospace-update-debug-done",
				"bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-installinit-installdisk-installbootfs-exception-downloadfail-update-debug-done",
				]:
			sequences.update({n : "restart_node_rins"})

		#	restart_node_boot
		for n in ["bminit-cfg-auth-getplc-implementerror-bootupdatefail-update-debug-done",
				 "bminit-cfg-auth-implementerror-bootcheckfail-update-debug-done",
				 "bminit-cfg-auth-implementerror-bootcheckfail-update-implementerror-bootupdatefail-done",
				 "bminit-cfg-auth-getplc-update-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nospace-update-debug-done",
				 "bminit-cfg-auth-getplc-hardware-installinit-installdisk-installbootfs-exception-downloadfail-update-debug-done",
				 "bminit-cfg-auth-getplc-update-installinit-validate-implementerror-update-debug-done",
				 "bminit-cfg-auth-getplc-exception-update-bootupdatefail-debug-done",
				 ]:
			sequences.update({n: "restart_node_boot"})

		# fsck_repair
		for n in ["bminit-cfg-auth-getplc-update-installinit-validate-fsckabort-exception-fsckfail-bmexceptmount-exception-noinstall-update-debug-validate-fsckabort-exception-fsckfail-bmexceptmount-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail-exception-noinstall-update-debug-validate-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-update-installinit-validate-exception-fsckfail-exception-noinstall-update-debug-validate-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-update-installinit-validate-exception-fsckfail2-exception-noinstall-update-debug-validate-exception-fsckfail2-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail2-exception-debug-validate-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail2-exception-debug-validate-exception-fsckfail2-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail2-exception-debug-validate-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-update-installinit-validate-fsckabort-exception-fsckfail-exception-debug-validate-fsckabort-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-update-installinit-validate-exception-fsckfail2-exception-debug-validate-exception-fsckfail2-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail-exception-debug-validate-exception-fsckfail2-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail-exception-debug-validate-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-installinit-validate-exception-fsckfail-exception-debug-validate-done",
				  "bminit-cfg-auth-getplc-update-installinit-validate-exception-fsckfail-exception-debug-validate-exception-fsckfail-done",
				  "bminit-cfg-auth-getplc-update-debug-validate-exception-fsckfail-done",
				]:
			sequences.update({n : "fsck_repair"})

		# nodeconfig_notice
		for n in ["bminit-cfg-exception-nocfg-update-bootupdatefail-nonode-debug-done",
				  "bminit-cfg-exception-update-bootupdatefail-nonode-debug-done",
				  "bminit-cfg-exception-update-bootupdatefail-nonode-debug-validate-exception-done",
				  "bminit-cfg-exception-nocfg-update-bootupdatefail-nonode-debug-validate-exception-done",
				  "bminit-cfg-auth-bootcheckfail-nonode-exception-update-bootupdatefail-nonode-debug-done",
				  "bminit-cfg-exception-noconfig-nonode-debug-validate-exception-done",
				  "bminit-cfg-exception-noconfig-update-debug-validate-exception-done",
				  "bminit-cfg-exception-noparseconfig-debug-validate-exception-done",
				  "bminit-cfg-exception-noconfig-debug-validate-exception-done",
				  "bminit-cfg-auth-authfail2-nonode-debug-done",
				]:
			sequences.update({n : "nodeconfig_notice"})

		for n in [ "bminit-cfg-exception-nodehostname-update-debug-done", 
				   "bminit-cfg-update-exception-nodehostname-update-debug-validate-exception-done",
				   "bminit-cfg-update-exception-nodehostname-update-debug-done", 
				   "bminit-cfg-exception-nodehostname-debug-validate-bmexceptvgscan-done",
				   "bminit-cfg-exception-nodehostname-debug-validate-exception-done",
				]:
			sequences.update({n : "nodenetwork_email"})

		# noblockdevice_notice
		for n in ["bminit-cfg-auth-getplc-update-hardware-exception-noblockdev-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-noblockdev-exception-hardwarerequirefail-update-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-hardware-exception-noblockdev-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-update-hardware-noblockdev-exception-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-noblockdev-exception-hardwarerequirefail-update-debug-done",
				"bminit-cfg-auth-getplc-hardware-noblockdev-exception-hardwarerequirefail-debug-validate-bmexceptvgscan-done",
				"bminit-cfg-auth-getplc-update-hardware-noblockdev-exception-hardwarerequirefail-debug-validate-bmexceptvgscan-done",
				]:
			sequences.update({n : "noblockdevice_notice"})

		# update_bootcd_email
		for n in [ "bminit-cfg-auth-getplc-hardware-exception-hardwarerequirefail-update-debug-done",
				]:
			sequences.update({n : "update_bootcd_email"})

		for n in [ "bminit-cfg-auth-getplc-installinit-validate-rebuildinitrd-netcfg-update3-implementerror-nofilereference-update-debug-done",
				]:
			sequences.update({n: "unknownsequence_notice"})

		# minimalhardware_notice
		for n in [ "bminit-cfg-auth-getplc-hardware-exception-disktoosmall-hardwarerequirefail-update-debug-done",
					"bminit-cfg-auth-getplc-hardware-disktoosmall-exception-hardwarerequirefail-update-debug-done",
					"bminit-cfg-auth-getplc-update-hardware-exception-hardwarerequirefail-debug-validate-bmexceptvgscan-done",
					"bminit-cfg-auth-getplc-hardware-exception-hardwarerequirefail-debug-validate-bmexceptvgscan-done",
				]:
			sequences.update({n: "minimalhardware_notice"})

		# baddisk_notice
		sequences.update({"bminit-cfg-auth-getplc-update-hardware-exception-hardwarerequirefail-update-debug-done" : "baddisk_notice"})

		# baddns_notice
		for n in [ 
		 "bminit-cfg-update-implementerror-bootupdatefail-dnserror-update-implementerror-bootupdatefail-dnserror-done",
			"bminit-cfg-auth-implementerror-bootcheckfail-dnserror-update-implementerror-bootupdatefail-dnserror-done",
			]:
			sequences.update( { n : "baddns_notice"})

		return sequences

sequences = getSequences()

for s in sequences:
	bms = BootmanSequenceRecord.get_by(sequence=s)
	if not bms:
		bms = BootmanSequenceRecord(sequence=s, action=sequences[s])
		bms.flush()

session.flush()
