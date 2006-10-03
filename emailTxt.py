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
   STANDARD="""As part of the monitoring of PlanetLab nodes, we have noticed that the node %(hostname)s is not responding to pings and is not available for ssh.

Please check the machine's connectivity and, if properly networked, power cycle the machine. If there are any console messages relating to the machines's failure, please pass those to the PlanetLab-support mailing list so we can resolve any problems.


Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""

   STANDARD_PI="""As part of the monitoring of PlanetLab nodes, we have noticed that the node %(hostname)s is not responding to pings and is not available for ssh. We have made several attempts to contact the techinical contacts for this site (they are CCed) to help us bring the node back online. If there should be a different technical contact appointed, you may add the 'tech' role to any user registered for your site via the website. (Manage Users off the left nav bar on the PI tab, then click the user)

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

We have attempted to reboot some nodes at your site that appear to be down and found that we were unable to connect to the power control unit. Could you please bring it back online? Certain units benefit from a power cycle. Occasionally the problem is that our information for the PCU is incorrect. If the unit seems fine, please verify that the information is correct by logging into the website and clicking the 'power control units' link in the lefthand nav bar. Please let us know if you run into problems.

Thanks.

  -- PlanetLab Central (support@planet-lab.org)
"""

   PCU_DOWN_PI="""Hello,

We have made several attempts to contact the techinical contacts for this site (they are CCed) to help us bring the node back online. If there should be a different technical contact appointed, you may add the 'tech' role to any user registered for your site via the website. (Manage Users off the left nav bar on the PI tab, then click the user)

We have attempted to reboot some nodes at your site that appear to be down and found that we were unable to connect to the power control unit. Could you please bring it back online? Certain units benefit from a power cycle. Occasionally the problem is that our information for the PCU is incorrect. If the unit seems fine, please verify that the information is correct by logging into the website and clicking the 'power control units' link in the lefthand nav bar. Please let us know if you run into problems.

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
