#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: emailTxt.py,v 1.9 2007/08/08 13:26:46 soltesz Exp $


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

To help, please confirm that a recent BootCD is installed in the machine (Version 3.0 or greater).  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.  Until that time, visiting the link below will return an 'Internal Server Error'.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new Boot CD and configuration file.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

If after following these directions and finding your machine reported by CoMon, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

After a week, we will disable your site's ability to create new slices.  Because this action will directly affect your site's registered PI, we will also CC the PI for help at that time.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	newdown_two=("""PlanetLab node(s) down: %(loginbase)s""", 
"""
Hello,

As part of PlanetLab node monitoring, we noticed the following nodes were down at your site:

%(hostname_list)s 
We're writing again because our previous correspondence, sent only to the registered Technical Contact, has gone unacknowledged for at least a week, and we need your help returning these machines to their regular operation.  We understand that machine maintenance can take time.  So, while we wait for the machines to return to their regular operation slice creation has been suspended at your site.  No new slices may be created, but the existing slices and services running within them will be unaffected.

To help, please confirm that a recent BootCD is installed in the machine (Version 3.0 or greater).  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new Boot CD and configuration file.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

If after following these directions and finding your machine reported by CoMon, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

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

To help, please confirm that a recent BootCD is installed in the machine (Version 3.0 or greater).  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the Comon status page to verify that your node is accessible from the network.  It may take several minutes before Comon registers your node.

	http://summer.cs.princeton.edu/status/tabulator.cgi?table=nodes/table_%(hostname)s&limit=50

If the machine has booted successfully, you may check it more quickly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new Boot CD and configuration file.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

If after following these directions and finding your machine reported by CoMon, there is no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")

	newbootcd_one=(""" Planetlab nodes need a new BootCD: %(loginbase)s""", # : %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

%(hostname_list)s  
This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (Either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

To check the status of these and any other machines that you manage please visit:

    http://comon.cs.princeton.edu/status

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

After a week, we will disable your site's ability to create new slices.  Because this action will directly affect your site's registered PI, we will also CC the PI for help at that time.

Thank you for your help,
  -- PlanetLab Central (support@planet-lab.org)
""")
	newbootcd_two=(""" Planetlab nodes need a new BootCD: %(loginbase)s""", # : %(hostname)s""", 
"""As part of PlanetLab node monitoring, we noticed the following nodes have an out-dated BootCD: 

%(hostname_list)s  
This usually implies that you need to update the BootCD and node configuration file stored on the read-only media (Either the all-in-one ISO CD, floppy disk, or write-protected USB stick).

We're writing again because our previous correspondence, sent only to the registered Technical Contact, has gone unacknowledged for at least a week, and we need your help returning these machines to their regular operation.  We understand that machine maintenance can take time.  So, while we wait for the machines to return to their regular operation, slice creation has been suspended at your site.  No new slices may be created, but the existing slices and services running within them will be unaffected.

To check the status of these and any other machines that you manage please visit:

    http://comon.cs.princeton.edu/status

Instructions to perform the steps necessary for a BootCD upgrade are available in the Technical Contact's Guide.

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

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

    https://www.planet-lab.org/doc/guides/tech#NodeInstallation

If your node returns to normal operation after following these directions, then there's no need to respond to this message.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue.  Including this message in your reply will help us coordinate our records with the actions you've taken.  

Thank you for your help,
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
	# TODO: need reminder versions for repeats...
	newdown=[newdown_one, newdown_two, newdown_three]
	newbootcd=[newbootcd_one, newbootcd_two, newbootcd_three]
	newthankyou=[thankyou,thankyou,thankyou]

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

	planet_cnf=(""" Planetlab node %(hostname)s needs an updated configuration file""", """As part of PlanetLab node monitoring, we noticed %(hostname)s has an out-dated planet.cnf file with no NODE_ID.  This can happen after an upgrade and requires your assistance in correcting.  All that is needed is to visit:

	https://www.planet-lab.org/db/nodes/index.php?id=%(node_id)d

And follow the "Download conf file" link to generate a new configuration file for each node.  Copy this file to the appropriate read-only media, either floppy or USB stick, and reboot the machines.

There's no need to respond to this message if you're able to update the configuration files without difficulty and your node returns to normal operation.  However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can help resolve the issue. 

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


	dns=("""Planetlab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed the DNS servers used by  %(hostname)s are not responding to queries.

Please verify the DNS information used by the node is correct.  You can find directions on how to update the node's network information on the PlanetLab Technical Contacts Guid (http://www.planet-lab.org/doc/TechsGuide.php#id268898).

Thanks.

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

