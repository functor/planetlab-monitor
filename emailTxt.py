#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: emailTxt.py,v 1.5 2007/01/10 20:08:44 faiyaza Exp $


# 
# Tis file contains the texts of the automatically generated
# emails sent to techs and PIs
#

class mailtxt:

	down=("""PlanetLab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s has been down for %(days)s days.

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page (http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s') to verify that your node is accessible from the network.

There's no need to respond to this message if CoMon reports that your machine is accessible. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can resolve the issue. 

Thanks.


  -- PlanetLab Central (support@planet-lab.org)
""")


	dbg=("""Planetlab node %(hostname)s requires reboot.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s is in debug mode.  This usually implies the node was rebooted unexpectedly and could not come up cleanly.  

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page (http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s') to verify that your node is accessible from the network.

There's no need to respond to this message if CoMon reports that your machine is accessible. However, if there are any console messages relating to the node's failure, please report them to PlanetLab support (support@planet-lab.org) so we can resolve the issue. 

Thanks.


  -- PlanetLab Central (support@planet-lab.org)
""")


	ssh=("""Planetlab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed node %(hostname)s is not available for ssh.

Please check the node's connectivity and, if properly networked, power cycle the machine. Note that rebooting the machine may not fully resolve the problems we're seeing. Once the machine has come back up, please visit the Comon status page (http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&select='address==%(hostbyteorder)s') to verify that your node is accessible from the network.

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

