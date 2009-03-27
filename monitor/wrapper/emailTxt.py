#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: emailTxt.py,v 1.10 2007/08/29 17:26:50 soltesz Exp $


# 
# This file contains the texts of the automatically generated
# emails sent to techs and PIs
#

class mailtxt:

	newdown_one=("""PlanetLab node(s) down: %(loginbase)s""", 
"""
Hello,

As part of PlanetLab node monitoring, we noticed the following nodes were down at your site:

%(hostname_list)s 
We're writing because we need your help returning them to their regular operation.

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.  Until that time, visiting the link below will return the message 'could not find requested table - probably empty'.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new BootImage on CD or USB.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

If after following these directions, and either logging in with your site_admin account or seeing the CoMon report of your machine, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

Finally, you can track the current status of your machines using this Google Gadget:

    http://fusion.google.com/add?source=atgs&moduleurl=http://monitor.planet-lab.org/monitor/sitemonitor.xml

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

#If no one responds, then after a week, we will disable your site's ability to create new slices.  Because this action will directly affect your site's registered PI, we will also CC the PI for help at that time.

	newdown_two=("""PlanetLab node(s) down: %(loginbase)s""", 
"""
Hello,

As part of PlanetLab node monitoring, we noticed the following nodes were down at your site:

%(hostname_list)s 
We're writing again because our previous correspondence, sent only to the registered Technical Contact, has gone unacknowledged for at least a week, and we need your help returning these machines to their regular operation.  We understand that machine maintenance can take time.  So, while we wait for the machines to return to their regular operation slice creation has been suspended at your site.  No new slices may be created, but the existing slices and services running within them will be unaffected.

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.  Until that time, visiting the link below will return the message 'could not find requested table - probably empty'.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new Boot CD and configuration file.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

If after following these directions, and either logging in with your site_admin account or seeing the CoMon report of your machine, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

Finally, you can track the current status of your machines using this Google Gadget:

    http://fusion.google.com/add?source=atgs&moduleurl=http://monitor.planet-lab.org/monitor/sitemonitor.xml

After another week, we will disable all slices currently running on PlanetLab.  Because this action will directly affect all users of these slices, these users will also be notified at that time.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	newdown_three=("""PlanetLab node(s) down: %(loginbase)s""", 
"""
Hello,

As part of PlanetLab node monitoring, we noticed the following nodes were down at your site:

%(hostname_list)s 
We understand that machine maintenance can take time.  We're writing again because our previous correspondences, sent first to the registered Technical Contact then the the Site PI, have gone unacknowledged for at least two weeks, and we need your help returning these machines to their regular operation.  This is the third time attempting to contact someone in regard to these machines at your site.  So, while we wait for the machines to return to their regular operation all current slice activity will be suspended.  Current experiments will be stopped and will not be be able to start again until there is evidence that you have begun to help with the maintenance of these machines.

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.  Until that time, visiting the link below will return the message 'could not find requested table - probably empty'.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new Boot CD and configuration file.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

Finally, you can track the current status of your machines using this Google Gadget:

    http://fusion.google.com/add?source=atgs&moduleurl=http://monitor.planet-lab.org/monitor/sitemonitor.xml

If after following these directions, and either logging in with your site_admin account or seeing the CoMon report of your machine, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	newbootcd_one=(""" Planetlab nodes need a new BootCD: %(loginbase)s""", # : %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

%(hostname_list)s  
This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

To check the status of these and any other machines that you manage please visit:

    http://comon.cs.princeton.edu/status

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/bootcdsetup

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
#After a week, we will disable your site's ability to create new slices.  Because this action will directly affect your site's registered PI, we will also CC the PI for help at that time.

	newbootcd_two=(""" Planetlab nodes need a new BootCD: %(loginbase)s""", # : %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

%(hostname_list)s  
This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (Either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

We're writing again because our previous correspondence, sent only to the registered Technical Contact, has gone unacknowledged for at least a week, and we need your help returning these machines to their regular operation.  We understand that machine maintenance can take time.  So, while we wait for the machines to return to their regular operation, slice creation has been suspended at your site.  No new slices may be created, but the existing slices and services running within them will be unaffected.

To check the status of these and any other machines that you manage please visit:

    http://comon.cs.princeton.edu/status

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/bootcdsetup

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

After another week, we will disable all slices currently running on PlanetLab.  Because this action will directly affect all users of these slices, these users will also be notified at that time.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
	newbootcd_three=(""" Planetlab nodes need a new BootCD: %(loginbase)s""", # : %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

%(hostname_list)s  
This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (Either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

We understand that machine maintenance can take time.  We're writing again because our previous correspondences, sent first to the registered Technical Contact then the the Site PI, have gone unacknowledged for at least two weeks, and we need your help returning these machines to their regular operation.  This is the third time attempting to contact someone in regard to these machines at your site.  So, while we wait for the machines to return to their regular operation all current slice activity will be suspended.  Current experiments will be stopped and will not be be able to start again until there is evidence that you have begun to help with the maintenance of these machines.

To check the status of these and any other machines that you manage please visit:

    http://comon.cs.princeton.edu/status

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/bootcdsetup

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
	pcuthankyou_one=("""Thank you for correcting your PlanetLab node PCU - %(loginbase)s""",
	"""
While monitoring your site, we noticed that the following PCU *improved* their states:

%(hostname_list)s  
Often, system administration is a thankless job, but not today. :-)

Thank you!
  -- PlanetLab Central (support@planet-lab.org)
	""")

	thankyou=("""Thank you for helping maintain your PlanetLab nodes - %(loginbase)s""",
	"""
While monitoring your site, we noticed that the following nodes *improved*
their states:

%(hostname_list)s  
Often, system administration is a thankless job, but not today. :-)

Thank you!
  -- PlanetLab Central (support@planet-lab.org)

Legend:
PROD-      This state is the production state where the node can contact PlanetLab, 
           and install slices from users.
DEBUG-     This state designates a node that could not boot successfully.
OLDBOOTCD- This state corresponds to the situation where an oldbootcd prevented 
           the normal operation of the node.
ERROR- 	   This is an error state, where there is absolutely no contact 
           with PlanetLab.
	""")

	pcufailed_notice =("""Could not use PCU to reboot %(hostname)s""",

"""As part of PlanetLab node monitoring and maintenance, we tried to use the PCU
registered for %(hostname)s, but could not for some reason.

Please help.

Thank you very much for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
	online_notice=("""Host %(hostname)s is online""",
	"""
This notice is simply to let you know that:
    %(hostname)s

is online and operational.  Thank you very much for your help!
	""")
	test_notice=("""Host %(hostname)s is testing""",
	"""
This notice is simply to test whether notices work.
    %(hostname)s

Thank you very much for your help!
	""")
	retry_bootman=("""Running BootManager on %(hostname)s""",
	"""
This notice is simply to let you know that:
    %(hostname)s

appears stuck in a debug mode.  To try to correct this, we're trying to rerun BootManager.py.  
If any action is needed from you, you will recieve additional notices.  Thank you!
	""")
	down_notice=("""Host %(hostname)s is down""",
	"""
This notice is simply to let you know that:
    %(hostname)s

is down, disconnected from the network and/or non-operational.  Please investigate, thank you very much for your help!
	""")

	clear_penalty=("""All penalties have been cleared from site %(loginbase)s""",
	"""
This notice is to let you know that any penalties previously applied to your site have 
been removed: %(penalty_level)s.

All privileges have been restored.  If your slices were disabled, please allow
up to 30 minutes for them to return to enabled.

Legend:

  0  - no penalties applied
  1  - site is disabled.  no new slices can be created.
  2+ - all existing slices will be disabled.
	""")

	increase_penalty=("""Penalty increased for site %(loginbase)s""",
	"""
This notice is to let you know that the penalty applied to your site has
increased: %(penalty_level)s.

legend:

  0  - no penalty applied
  1  - site is disabled.  no new slices can be created.
  2+ - all existing slices will be disabled.
	""")

	newbootcd_notice=(""" Host %(hostname)s needs a new BootImage""", """
As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

    %(hostname)s  

This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	nmreset =("""NM Reset at %(loginbase)s""",
	"""
Monitor restarted NM on the following machines:

%(hostname_list)s  

	""")
	pcudown_one =("""Could not use PCU to reboot %(hostname)s""",

"""As part of PlanetLab node monitoring and maintenance, we tried to use the PCU
registered below, but could not for the reasons at the link below:

	https://monitor.planet-lab.org/cgi-bin/printbadpcus.php?id=%(pcu_id)s

We need your help resolving this issue in a few ways:  

 1. First, we need your help rebooting %(hostname)s.  Because the above PCU does 
    not appear to work, please manually reboot this machine.  If it turns out that 
    there is a problem with the PCU configuration, we can help you
    resolve that independently.

 2. If there is nothing apparently wrong with the PCU, or the mapping between
    the PCU and the host, then there is likely a problem with our bootstrap
    software on your machine.  To help us, please make a note of any text on
    the console and report it to mailto:support@planet-lab.org .  An example
    might be that the console hangs waiting for a module to unload.  The last
    reported name or any error messages on the screen would be very helpful.

 3. Alternately, if it is possible, please correcct the above PCU problem, or
    let us know what steps you are taking.  By enabling us to take administrative 
    actions automatically from PlanetLab Central without your intervention, you 
    can trade a small amount of time now for a time savings in the future. 

If the PCU is up and running, but behind a firewall, please make it accessible
from address block 128.112.139.0/24.  You can confirm that this is the address
space from which the PlanetLab Central servers run.

If the above PCU is no longer in service, please delete it by visiting:

    https://www.planet-lab.org/db/sites/pcu.php?id=%(pcu_id)s

and selecting 'Delete PCU'. You may then register a new PCU for your nodes.

Thank you very much for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
	pcutonodemapping_one =("""PCU to Node mapping is incorrect for %(hostname)s""",
	"""
    As part of our machine monitoring and maintenance, we tried to use the PCU
registered below, and though it appears to succeed, we do not subsequently
observe the associated nodes rebooting:

    https://monitor.planet-lab.org/cgi-bin/printbadpcus.php?id=%(pcu_id)s

%(hostname_list)s

We need your help resolving this issue in two ways:  

* First, we need your help rebooting %(hostname)s.  Because the above PCU 
  does not appear to actually control the above Nodes, we cannot use it to
  reboot these machines. So, please manually reboot the machine and we can 
  help you resolve any configuration errors with the PCU independently.

* Second, please check the configuration of the above PCU.  Check that the 
  PCU is physically connected to the servers that it should be able to
  control.  A common mistake is that the PCU is registered for a machine, 
  but not actually connected physically to the machine. 

By enabling us to take administrative actions automatically from PlanetLab
Central without local intervention, you can trade a small amount of time now
for a time savings in the future. 
    
If the above PCU is no longer in service, please delete it by visiting:

    https://www.planet-lab.org/db/sites/pcu.php?id=%(pcu_id)s

and selecting 'Delete PCU'. You may then register a new PCU for your nodes.

Alternately, if the machines listed above are no longer in service, please
delete them by visiting your sites page at:

    https://www.planet-lab.org/

Thank you very much for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	newalphacd_notice=(""" New Boot Images for %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed that your machine needs a new BootCD to fully support your hardware: 

%(hostname)s  

To make this process as simple as possible, we have created All-in-One boot images that include the node configuration file.  

The only step that you need to take is to choose which media you prefer, either CD ISO, or USB image for each host.

%(url_list)s

Instructions to burn or copy these All-in-One images to the appropriate media are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/bootcdsetup

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	# TODO: need reminder versions for repeats...
	newdown=[newdown_one, newdown_two, newdown_three]
	newbootcd=[newbootcd_one, newbootcd_two, newbootcd_three]
	#newalphacd=[newalphacd_one, newalphacd_one, newalphacd_one]
	newthankyou=[thankyou,thankyou,thankyou]
	pcuthankyou=[pcuthankyou_one,pcuthankyou_one,pcuthankyou_one]
	NMReset=[nmreset,nmreset,nmreset]
	pcutonodemapping=[pcutonodemapping_one, pcutonodemapping_one, pcutonodemapping_one]
	pcudown=[pcudown_one, pcudown_one, pcudown_one]

	unknownsequence_notice = ("""Unrecognized Error on PlanetLab host %(hostname)s""", 
					   """
While trying to automatically recover this machine:

    http://www.planet-lab.org/db/nodes/index.php?nodepattern=%(hostname)s

We encountered an unknown situation.  Please re-code to handle, or manually intervene to repair this host.

Abbreviated BootManager Sequence:

    %(sequence)s

BootManager.log output follows:
---------------------------------------------------------
%(bmlog)s
"""	  )
	donation_down_one=("""PlanetLab node donation setup: %(hostname)s""", 
	"""
Hello,

As part of PlanetLab node monitoring, we noticed the following node is registered in the PlanetLab database, but it is not completly setup and running.

%(hostname_list)s 
We are writing because we need your help completing the setup to ensure its full operation.

You should have received directions for the complete configuration when you contacted the donation program coordinator at PlanetLab.  For review, or if you did not receive them, you can find the latest version here:

    https://svn.planet-lab.org/wiki/DC7800Configuration

It is essential that the AMT feature be configured to enable PlanetLab staff to remotely manage the machine.  The basic steps are:

    Configure the DC7800 AMT feature  : https://www.planet-lab.org/AMT
    Add a PCU to your site            : https://www.planet-lab.org/db/sites/pcu.php
	Associate your node with the PCU  : Follow the 'My Site' link
	Finally, download the Boot Image  : https://www.planet-lab.org/db/nodes/index.php?nodepattern=%(hostname)s
	Burn Boot Image to media & Reboot your node

You can confirm that your machine's PCU is correctly configured by visiting the AMT
port using your browser, such as:

    http://%(hostname)s:16992/

If you need any clarification about the steps mentioned here, please feel free
to contact us at PlanetLab Support (support@planet-lab.org).

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	donation_nopcu_one=("""PlanetLab node donation, PCU setup: %(hostname)s""", 
"""
Hello,

As part of PlanetLab node monitoring, we noticed the following node was not completely setup at your site:

%(hostname_list)s 
We are writing because we need your help completing the setup to ensure its full operation.

The DC7800 comes with a built-in remote management feature.  The PCU functionality on your node is not configured.  The result of this is that we are unable to remotely administer this machine.

You should have received directions for the complete configuration when you contacted the donation program coordinator at PlanetLab.  For review, or if you did not receive them, you can find the latest version here:

    https://svn.planet-lab.org/wiki/DC7800Configuration

It is essential that the PCU be configured.  The basic steps are:

    Configure the DC7800 AMT feature  : https://www.planet-lab.org/AMT
    Add a PCU to your site            : https://www.planet-lab.org/db/sites/pcu.php
	Associate your node with the PCU  : Follow the 'My Site' link

You can confirm that your machine is correctly configured by visiting the AMT
port using your browser, such as:

    http://%(hostname)s:16992/

If you need any clarification about the steps mentioned here, please feel free
to contact us at PlanetLab Support (support@planet-lab.org).

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	donation_nopcu = [ donation_nopcu_one, donation_nopcu_one, donation_nopcu_one ]
	donation_down = [ donation_down_one, donation_down_one, donation_down_one ]


	minimalhardware_notice = ("""Hardware requirements not met on PlanetLab host %(hostname)s""", 
					   """
While trying to automatically recover this machine:

    http://www.planet-lab.org/db/nodes/index.php?nodepattern=%(hostname)s

We encountered an failed hardware requirement.  Please look at the log below to determine the exact nature of the failure, either Disk, CPU, Network, or Mimial RAM was not satisfied.

If your machine does not meet the current hardware specifications for a PlanetLab node (http://www.planet-lab.org/hardware), please upgrade it to meet the current recommended configuration.  

If you believe this message is an error, please email support@planet-lab.org explaining the problem.  You may need to create an updated Boot Image that includes drivers for your hardware.

Thank you,
 - PlanetLab Support

BootManager.log output follows:
---------------------------------------------------------
%(bmlog)s
"""	  )

	baddisk_notice = ("""Bad Disk on PlanetLab node %(hostname)s""", 
			   """As part of PlanetLab node monitoring, we noticed %(hostname)s has a number of disk or media related I/O errors, that prevent it from either booting or reliably running as a PlanetLab node.

Please verify the integrity of the disk, and order a replacement if needed.  If you need to schedule downtime for the node, please let us know at support@planet-lab.org. 

Thanks.

  -- PlanetLab Central (support@planet-lab.org)

The output of `dmesg` follows:
-------------------------------------------------------------------------

%(log)s
""")

	down=("""PlanetLab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s has been down for %(days)s days.

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.

http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s'

http://www.planet-lab.org/db/sites/index.php?id=%(site_id)d

There's no need to respond to this message if CoMon reports that your machine is accessible. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can resolve the issue. 

Thanks.


  -- PlanetLab Central (support@planet-lab.org)
""")

	dbg=("""Planetlab node %(hostname)s requires reboot.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s is in debug mode.  This usually implies the node was rebooted unexpectedly and could not come up cleanly.  

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.

http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s'

There's no need to respond to this message if CoMon reports that your machine is accessible. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can resolve the issue. 

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	plnode_cfg=(""" Please Verify Network Configuration for PlanetLab node %(hostname)s""", 
"""Hello,

As part of PlanetLab node monitoring, we noticed that %(hostname)s has a network configuration error related to DNS or hostname lookups.  Often this can happen either due local configuraiton changes, or a misconfiguration of the node's DNS servers.  To resolve the issue we require your assistance.  All that is needed is to visit:

	https://www.planet-lab.org/db/nodes/index.php?nodepattern=%(hostname)s

Find the primary node network entry and confirm that the settings are correct.  

If you use 'static' network configuration, verify that the DNS servers are correct.  If you are using 'dhcp' then you will need to confirm that the information returned for the node will allow it to perform lookups on it's own hostname.

If you change the network settings, then select, "Download -> Download plnode.txt file for %(hostname)s" menu.  This will generate a new configuration file for your node.  Copy this file to the appropriate read-only media, either floppy or USB stick, and reboot the machine.  If you are using an All-in-One boot image, then you will need to download the All-in-One image instead, burn it to the appropriate media (CD or USB) and reboot.

Please let us know if you need any assistance.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)

BootManager.log output follows:
---------------------------------------------------------
%(bmlog)s
""")

	nodeconfig_notice=(""" Please Update Configuration file for PlanetLab node %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed %(hostname)s has an out-dated plnode.txt file with no NODE_ID or a mis-matched HOSTNAME.  This can happen either due to an initial configuration failure at your site, with information entered into our database, or after a software upgrade.  To resolve the issue we require your assistance.  All that is needed is to visit:

	https://www.planet-lab.org/db/nodes/index.php?nodepattern=%(hostname)s

Then, select, "Download -> Download plnode.txt file for %(hostname)s" menu.  This will generate a new configuration file for your node.  Copy this file to the appropriate read-only media, either floppy or USB stick, and reboot the machine.

There is no need to respond to this message if you're able to update the configuration file without difficulty and your node returns to normal operation.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue. 

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	bootcd=(""" Planetlab node %(hostname)s needs a new BootCD""", 
"""As part of PlanetLab node monitoring, we noticed %(hostname)s has an out-dated BootCD: "%(version)".  This usually implies that you need to update both the BootCD and regenerate the planet.cnf file stored on the read-only floppy (Or read-only USB stick that stores the content of BootCD and planet.cnf).

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact Guide.
    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

There's no need to respond to this message if you're able to follow the directions without difficulty and your node returns to normal operation. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue. 

Thanks you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	ssh=("""Planetlab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed node %(hostname)s is not available for ssh.

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.

http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s'

There's no need to respond to this message if CoMon reports that your machine is accessible. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can resolve the issue. 

Thanks.


  -- PlanetLab Central (support@planet-lab.org)
""")


	baddns_notice=("""Planetlab node down: broken DNS configuration for %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the DNS servers used by the following machine(s) are not responding to queries.

    %(hostname)s 

The conseuqnece of this is that the node cannot boot correctly, and is not a functioning part of the PlanetLab network.

To help us return this machine to running order, please verify that the registered DNS servers in the node network configuration are correct.  

%(network_config)s

You may update the node's network information at the link below:

    https://www.planet-lab.org/db/nodes/node_networks.php?id=%(nodenetwork_id)s

If you have any questions, please feel free to contact us at PlanetLab Support (support@planet-lab.org).

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")


	filerw=("""Planetlab node %(hostname)s has a bad disk.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s has a read-only filesystem.

Please verify the integrity of the disk and email the site if a replacement is needed. 

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
""")


	clock_drift=("""Planetlab node %(hostname)s and NTP.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s cannot reach our NTP server.

Please verify that the NTP port (tcp/123) is not blocked by your site. 

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
""")

  

	removedSliceCreation=("""PlanetLab slice creation/renewal suspension.""","""As part of PlanetLab node monitoring, we noticed the %(loginbase)s site has less than 2 nodes up.  We have attempted to contact the PI and Technical contacts %(times)s times and have not received a response.  

Slice creation and renewal are now suspended for the %(loginbase)s site.  Please be aware that failure to respond will result in the automatic suspension of all running slices on PlanetLab.


  -- PlanetLab Central (support@planet-lab.org)
""")


	suspendSlices=("""PlanetLab slices suspended.""","""As part of PlanetLab node monitoring, we noticed the %(loginbase)s site has less than 2 nodes up.  We have attempted to contact the PI and Technical contacts %(times)s times and have not received a response.  

All %(loginbase)s slices are now suspended.  


  -- PlanetLab Central (support@planet-lab.org)
""")


	pcu_broken=("""%(hostname)s failed to reinstall""","""Hello,

   %(hostname)s was remotely rebooted via your power control unit but has not contacted PlanetLab since. It should contact upon every boot, hence we believe that either the node has some hardware problems, is not properly connected to the power control unit, or has network connectivity issues. Could you please reboot the node and watch the console for error messages? 


Thanks.

-- PlanetLab Central (support@planet-lab.org)
""")


	no_pcu=("""Hello,

We have set %(hostname)s to reinstall, but because your site does not have a power control unit, we are unable to powercycle the node.  Please  

Thanks.

-- PlanetLab Central (support@planet-lab.org)
""")

