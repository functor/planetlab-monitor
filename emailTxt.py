#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $


# 
# Tis file contains the texts of the automatically generated
# emails sent to techs and PIs
#

class mailtxt:
   dbg=("""PlanetLab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed node %(hostname)s has been down for some time.

Please check the node's connectivity and, if properly networked, power cycle the machine. If there are any console messages relating to the node's failure, please pass those to the PlanetLab-support mailing list so we can resolve the issue.


Thanks.

  -- PlanetLab Central (support@planet-lab.org)
""")

   down=("""PlanetLab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed node %(hostname)s has been down for some time.

Please check the node's connectivity and, if properly networked, power cycle the machine. If there are any console messages relating to the node's failure, please pass those to the PlanetLab-support mailing list so we can resolve the issue.


Thanks.

  -- PlanetLab Central (support@planet-lab.org)
""")

   ssh=("""Planetlab node %(hostname)s down.""", """As part of PlanetLab node monitoring, we noticed node %(hostname)s is not available for ssh.

Please check the node's connectivity and, if properly networked, power cycle the machine. If there are any console messages relating to the node's failure, please pass those to the PlanetLab-support mailing list so we can resolve the issue.


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


   dbg=("""Planetlab node %(hostname)s requires reboot.""", """As part of PlanetLab node monitoring, we noticed %(hostname)s is in debug mode.  This usually implies the node was rebooted unexpectedly and could not come up cleanly.  

We have set the node to reinstall upon reboot.  Please reboot the machine.  It would be helpful if you could forward any error messages on the console to support@planet-lab.org.


Thanks.

  -- PlanetLab Central (support@planet-lab.org)
""")


   STANDARD_PI="""As part of PlanetLab nodes monitoring, we noticed the node %(hostname)s is not available for ssh. We have made several attempts to contact the techinical contacts for this site (they are CCed) to help us bring the node back online. If there should be a different technical contact appointed, you may add the 'tech' role to any user registered for your site via the website. (Manage Users off the left nav bar on the PI tab, then click the user)

Our records indicate that there is no remote power control unit connected to this node. If this is not the case, please log into the PlanetLab Website and update the PCU information.

https://www.planet-lab.org/db/pcu/

Please check the machine's connectivity and, if properly networked, power cycle the machine to reboot it. If there are any console messages relating to the machines's failure, please pass those to the PlanetLab-support mailing list so we can resolve any problems.


Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""

   PCU_DOWN="""Hello,

IMPORTANT: PLC has recently upgraded their monitoring system. One significant change is that PCU reboot attempts may now come from the following subnet:
128.112.154.64/26
If you have source IP filtering on your PCU please add this subnet.

We attempted to reboot nodes at your site that appear to be down and were unable to connect to the power control unit. Could you please check and verify its network connectivity? Certain units benefit from a power cycle. Occasionally the problem is that othe network information for the PCU is incorrect on the PL website. If the unit seems fine, please verify that the information is correct by logging into the website and clicking the 'power control units' link in the lefthand navigation bar. Please let us know if experience any problems.

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""


   PCU_INEFFECTIVE="""Hello,

%(hostname)s was remotely rebooted via your power control unit but has not contacted PlanetLab since. It should contact upon every boot, hence we believe that either the node has some hardware problems, is not properly connected to the power control unit, or has network connectivity issues. Could you please reboot the node and watch the console for error messages? 'Couldn't resolve bootX.planet-lab.org' usualy mean connectivity problems. This could be either network configuration or occasionally filtering by the local network admins due to unusual traffic.

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""

   PCU_INEFFECTIVE_PI="""Hello,

We have made several attempts to contact the techinical contacts for this site (they are CCed) to help us bring the node back online. If there should be a different techinical contact appointed, you may add the 'tech' role to any user registered for your site via the website. (Manage Users off the left nav bar on the PI tab, then click the user)

%(hostname)s was remotely rebooted via your power control unit but has not contacted PlanetLab since. It should contact upon every boot, hence we believe that either the node has some hardware problems, is not properly connected to the power control unit, or has network connectivity issues. Could you please reboot the node and watch the console for error messages? 'Couldn't resolve bootX.planet-lab.org' usually indicates connectivity problems. This could be either network configuration or occasionally filtering by the local network admins due to unusual traffic.

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""
