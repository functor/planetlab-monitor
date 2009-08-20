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

	thankyou=("""Thank you for helping maintain your PlanetLab nodes - %(loginbase)s""",
	"""
While monitoring your site, we noticed that the following nodes *improved*
their states:

%(hostname_list)s  
Often, system administration is a thankless job, but not today. :-)

Thank you!
  -- %(plc_name)s (%(support_email)s)

Legend:
PROD-      This state is the production state where the node can contact PlanetLab, 
           and install slices from users.
DEBUG-     This state designates a node that could not boot successfully.
OLDBOOTCD- This state corresponds to the situation where an oldbootcd prevented 
           the normal operation of the node.
ERROR- 	   This is an error state, where there is absolutely no contact 
           with PlanetLab.
	""")

#############################################################################
#############################################################################
#############################################################################

	pcumissing_notice =("""There is no PCU available to reboot %(hostname)s""",
"""We've noticed that there is no PCU associated with %(hostname)s, so we could 
not reboot it ourselves.

By taking a few moments now to register your PCU for this host, you will save
time in the future the next time we need to reboot this machine, because we
will be able to do so without disturbing you.

    http://%(plc_hostname)s/registerwizard/index.php

The registration is very quick.  All we need are: PCU hostname, IP, username, 
and password.  Then, choose which node to associate it with, and we will take 
care of the rest.

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	pcuerror_notice=("""Please help us configure your PCU: %(pcu_name)s""",
"""During our standard monitoring of your site we noticed that the following
PCU is misconfigured:

    %(pcu_name)s
	%(pcu_errors)s
You can learn more details about the problem by visiting the link below.

    https://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

We would like to save you time by taking care of as many administrative situations for your site's machines as possible without disturbing you.  Errors like these prevent us from being able to remotely administer your machines, and so we must solicit your help using messages like these.

So, any help and time that you can offer now to help us remotely administer your machines will pay off for you in the future.

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	pcufailed_notice =("""Could not use PCU to reboot %(hostname)s""",

"""We tried to use the PCU registered for %(hostname)s, but for some reason the host did not come back online.  This may be for several reasons, and you can learn more by visiting this link:

    %(pcu_name)s

    https://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

We need your help resolving this issue in a few ways:  

 1. First, we need your help rebooting %(hostname)s.  Because the above PCU does 
    not appear to work, please manually reboot this machine.  If it turns out 
    that there is a problem with the PCU configuration, we can help you
    resolve that independently.

 2. If it is possible, please correct the above PCU problem, or let us know
    what steps you are taking.  By enabling us to take administrative actions
    automatically without your intervention, you will save time in the future 
    the next time we need to reboot this machine, because we will be able to 
    do so without disturbing you.

 3. If there is nothing apparently wrong with the PCU, or the mapping between
    the PCU and the host, then there is likely a problem with our bootstrap
    software on your machine.  To help us, please make a note of any text on
    the console and report it to mailto:%(support_email)s .  An example
    might be that the console hangs waiting for a module to unload.  The last
    reported name or any error messages on the screen would be very helpful.

If the PCU is up and running, but behind a firewall, please make it accessible
from address block 128.112.139.0/24.  You can confirm that this is the address
space from which the %(plc_name)s servers run.

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	online_notice=("""Host %(hostname)s is online""",
	"""
This notice is simply to let you know that:
    %(hostname)s

is online and operational.  

    http://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

Thank you very much for your help!
  -- %(plc_name)s (%(support_email)s)
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
	firewall_notice=("""Host %(hostname)s blocked by a firewall""",
	"""
This notice is simply to let you know that:
    %(hostname)s

has some ports that appear to be blocked, making the node unusable.  While
some ports are open, a fully functional node needs all ports accessible at all
times.  Please see the following for the list of requirements for hosting a
node:

    http://www.planet-lab.org/hosting

We will consider the node 'DOWN' until the ports are unblocked.

Please investigate and let us know if there's anything we can do to help get
it back on-line.  You can see more information about the current status of
this host here:

    http://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
	""")
	down_notice=("""Host %(hostname)s is down""",
	"""
This notice is simply to let you know that:
    %(hostname)s

is down, disconnected from the network and/or non-operational.  

Please investigate, and let us know if there's anything we can do to help get
it back on-line.  You can see more information about the current status of
this host here:

    http://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
	""")

	clear_penalty=("""All privileges restored to site %(loginbase)s""",
	"""
This notice is to let you know that any privileges previously reduced at your 
site have been restored: %(penalty_level)s.

All privileges are restored.  You may create slices again, and if your 
slices were disabled, please allow up to 30 minutes for them to return to 
enabled.

    http://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)

Legend:

  0  - no penalties applied
  1  - site is disabled.  no new slices can be created.
  2+ - all existing slices will be disabled.
	""")

	increase_penalty=("""Privilege reduced for site %(loginbase)s""",
	"""
This notice is to let you know that the privileges granted to your site as
a participating member of Planetlab have reduced: %(penalty_level)s.

Your privileges will be reduced corresponding to the legend below.  To 
restore these privileges, please return at least two machines to working 
state.

    http://%(monitor_hostname)s/monitor/pcuview?loginbase=%(loginbase)s

Thank you very much for your help,
  -- %(plc_name)s (%(support_email)s)
  
Legend:

  0  - no penalty applied
  1  - site is disabled.  no new slices can be created.
  2+ - all existing slices will be disabled.
	""")

	newbootcd_notice=("""Host %(hostname)s needs a new BootImage""", """
We noticed the following node has an out-dated BootImage: 

    %(hostname)s  

This usually implies that you need to update the BootImage and node
configuration file stored on the read-only media (either the all-in-one ISO
CD, floppy disk, or write-protected USB stick).

You can do this by walking through the steps of the registration wizard, and
downloading a new BootImage for your machine.

    https://%(plc_hostname)s/registerwizard/index.php

Thank you for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	noblockdevice_notice=("""Cannot Detect Disks on %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed that we were not able to detect any hard disks in your machine.  

    %(hostname)s  

This may be the case for a number of reasons:
    * the hardware is very new and needs a new driver,
    * the hardware is very old is no longer supported,
    * the hard disk was physically removed, 
    * the hard disk cable is loose or disconnected,

Please help us investigate and let us know if there's anything that we can do to assist in getting your machine up and running again.

Thank you for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	newalphacd_notice=("""New Boot Images for %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed that we were not able to recognize all the hardware in your machine.  This means that either it is so new that it needs a new BootCD, or that it is so old that it is no longer supported.

    %(hostname)s  

To make this process as simple as possible, we have created All-in-One boot images that include the node configuration file.  

The only step that you need to take is to choose which media you prefer, either CD ISO, or USB image for each host.

%(url_list)s

Instructions to burn or copy these All-in-One images to the appropriate media are available in the Technical Contact's Guide.

    https://%(plc_hostname)s/doc/guides/bootcdsetup

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (%(support_email)s) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

Thank you for your help,
  -- %(plc_name)s (%(support_email)s)
""")


	# TODO: need reminder versions for repeats...
	#newdown=[newdown_one, newdown_two, newdown_three]
	#newbootcd=[newbootcd_one, newbootcd_two, newbootcd_three]
	#newalphacd=[newalphacd_one, newalphacd_one, newalphacd_one]
	#newthankyou=[thankyou,thankyou,thankyou]
	#pcuthankyou=[pcuthankyou_one,pcuthankyou_one,pcuthankyou_one]
	#pcutonodemapping=[pcutonodemapping_one, pcutonodemapping_one, pcutonodemapping_one]
	#pcudown=[pcudown_one, pcudown_one, pcudown_one]

	unknownsequence_notice = ("""Unrecognized Error on PlanetLab host %(hostname)s""", 
					   """
While trying to automatically recover this machine:

    http://%(plc_hostname)s/db/nodes/index.php?pattern=%(hostname)s
    https://%(monitor_hostname)s/monitor/pcuview?hostname=%(hostname)s

We encountered an unknown situation.  Please re-code to handle, or manually intervene to repair this host.

Abbreviated BootManager Sequence:

    %(sequence)s

BootManager.log output follows:
---------------------------------------------------------
%(bmlog)s
"""	  )


	minimalhardware_notice = ("""Hardware requirements not met on PlanetLab host %(hostname)s""", 
					   """
While trying to automatically recover this machine:

    http://%(plc_hostname)s/db/nodes/index.php?pattern=%(hostname)s

We encountered an failed hardware requirement.  Please look at the log below to determine the exact nature of the failure, either Disk, CPU, Network, or Mimial RAM was not satisfied.

If your machine does not meet the current hardware specifications for a PlanetLab node (http://%(plc_hostname)s/hardware), please upgrade it to meet the current recommended configuration.  

If you believe this message is an error, please email %(support_email)s explaining the problem.  You may need to create an updated Boot Image that includes drivers for your hardware.

Thank you,
 - PlanetLab Support

BootManager.log output follows:
---------------------------------------------------------
%(bmlog)s
"""	  )

	baddisk_notice = ("""Bad Disk on PlanetLab node %(hostname)s""", 
			   """As part of PlanetLab node monitoring, we noticed %(hostname)s has a number of disk or media related I/O errors, that prevent it from either booting or reliably running as a PlanetLab node.

Please verify the integrity of the disk, and order a replacement if needed.  If you need to schedule downtime for the node, please let us know at %(support_email)s. 

Thanks.

  -- %(plc_name)s (%(support_email)s)

The output of `dmesg` follows:
-------------------------------------------------------------------------

%(log)s
""")


	nodeconfig_notice=(""" Please Update Configuration file for PlanetLab node %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed %(hostname)s has an out-dated plnode.txt file.  

Either our boot scripts cannot find it because the boot media is corrupted, or it has no NODE_ID or a mis-matched HOSTNAME.  This can happen either due to a configuration mistake at your site, with bad information entered into our database, or after a necessary software upgrade.  To resolve the issue we require your assistance.  All that is needed is to visit:

    https://%(plc_hostname)s/db/nodes/index.php?pattern=%(hostname)s

Then double check the network settings for your host.

Then, select, "Download -> Download ISO image for %(hostname)s" menu.  This will generate a new All-in-one BootImage file for your node.  Copy this file to the appropriate read-only media, and reboot the machine.

There is no need to respond to this message. If you're able to update the boot image without difficulty and your node returns to normal operation, please accept our thanks.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (%(support_email)s) so we can help resolve the issue. 

Thank you for your help,
  -- %(plc_name)s (%(support_email)s)
""")

	baddns_notice=("""Planetlab node down: broken DNS configuration for %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the DNS servers used by the following machine(s) are not responding to queries.

    %(hostname)s 

The conseuqnece of this is that the node cannot boot correctly, and is not a functioning part of the PlanetLab network.

To help us return this machine to running order, please verify that the registered DNS servers in the node network configuration are correct.  

%(network_config)s

You may update the node's network information at the link below:

    https://%(plc_hostname)s/db/nodes/node_networks.php?id=%(interface_id)s

If you have any questions, please feel free to contact us at PlanetLab Support (%(support_email)s).

Thank you for your help,
  -- %(plc_name)s (%(support_email)s)
""")

#############################################################################
#############################################################################
#############################################################################


	filerw=("""Planetlab node %(hostname)s has a bad disk.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s has a read-only filesystem.

Please verify the integrity of the disk and email the site if a replacement is needed. 

Thanks.

  -- %(plc_name)s (%(support_email)s)
""")


	clock_drift=("""Planetlab node %(hostname)s and NTP.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s cannot reach our NTP server.

Please verify that the NTP port (tcp/123) is not blocked by your site. 

Thanks.

  -- %(plc_name)s (%(support_email)s)
""")

