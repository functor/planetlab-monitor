class mailtxt:
	@classmethod
	def reformat(cls, arguments={'hostname' : "your.host.name", 
								 'support_email' : 'support@your.host.name'}):
		fields = dir(cls)
		for f in fields:
			#print "looking at %s" % f
			if "__" not in f and 'reformat' not in f:
				attr = getattr(cls,f)
				#print attr
				setattr(cls, f, attr % arguments)
				#print getattr(cls,f)
		return

	nodedown_one_subject="Server {HOSTNAME} is unreachable: First Notice"
	nodedown_one = """
Hello,

We hope that you're having a good day.  As part of PlanetLab node monitoring, we noticed the following node is down at your site:

    {HOSTNAME} : Since {EVENT.AGE}

We're writing because we need your help returning them to their regular operation.

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the monitor status page to verify that your node is accessible.  

If the machine has booted successfully, you may check directly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new BootImage on CD or USB.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

There is no need to respond to this message unless there are any console messages relating to the node's failure.  In this case, please report them to PlanetLab support (%(support_email)s) so we can help resolve the issue.   Including this message in your reply will help us coordinate our records with the actions you've taken.

Finally, you can track the current status of your machines using this Google Gadget:

    http://fusion.google.com/add?source=atgs&moduleurl=http://%(hostname)s/monitor/sitemonitor.xml

Thank you for your help,
  -- PlanetLab Central (%(support_email)s)
"""

	nodedown_two_subject="Server {HOSTNAME} is unreachable: Second Notice"
	nodedown_two = """
Hello, 

We hope that you're having a good day.  As part of PlanetLab node monitoring, we noticed the following node is down at your site:

    {HOSTNAME} : Since {EVENT.AGE}

We're writing again because our previous correspondence, sent only to the registered Technical Contact, has gone unacknowledged for at least a week, and we need your help returning these machines to their regular operation.  We understand that machine maintenance can take time.  So, while we wait for the machines to return to their regular operation slice creation has been suspended at your site.  No new slices may be created, but the existing slices and services running within them will be unaffected.

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the monitor status page to verify that your node is accessible.  

If the machine has booted successfully, you may check directly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax                                                                                  
If you have a BootCD older than 3.0, you will need to create a new BootImage on CD or USB.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

If after following these directions, you are still experiencing problems, then you can acknowledge this notice by visiting, and letting us know what the problem is at mailto:%(support_email)s 

    http://%(hostname)s/zabbix/acknow.php?eventid={EVENT.ID}
    http://%(hostname)s/zabbix/tr_events.php?triggerid={TRIGGER.ID}&eventid={EVENT.ID}

After another week, we will disable all slices currently running on PlanetLab.  Because this action will directly affect all users of these slices, these users will also be notified at that time.

Thank you for your help,
  -- PlanetLab Central (%(support_email)s)


"""

	nodedown_three_subject="Server {HOSTNAME} is unreachable: Third Notice"
	nodedown_three ="""
Hello,

We hope that you're having a good day.  As part of PlanetLab node monitoring, we noticed the following node is down at your site:

    {HOSTNAME} : Since {EVENT.AGE}

We understand that machine maintenance can take time.  We're writing again because our previous correspondences, sent first to the registered Technical Contact then the the Site PI, have gone unacknowledged for at least two weeks, and we need your help returning these machines to their regular operation.  This is the third time attempting to contact someone in regard to these machines at your site.  So, while we wait for the machines to return to their regular operation all current slice activity will be suspended.  Current experiments will be stopped and will not be be able to start again until there is evidence that you have begun to help with the maintenance of these machines.  

To help, please confirm that a verison 3.0 or greater BootCD is installed in the machine.  Then, after checking that the node is properly networked, power cycle the machine.  Note that rebooting the machine may not fully resolve the problems we are seeing.  Once the machine has come back up, please visit the monitor status page to verify that your node is accessible.

If the machine has booted successfully, you may check directly by logging in with your site_admin account, and running:

    sudo /usr/sbin/vps ax

If you have a BootCD older than 3.0, you will need to create a new BootImage on CD or USB.  You can find instructions for this at the Technical Contact's Guide:

    https://www.planet-lab.org/doc/guides/bootcdsetup

If after following these directions, you are still experiencing problems, then you can acknowledge this notice by visiting, and letting us know what the problem is at mailto:%(support_email)s

    http://%(hostname)s/zabbix/acknow.php?eventid={EVENT.ID}
    http://%(hostname)s/zabbix/tr_events.php?triggerid={TRIGGER.ID}&eventid={EVENT.ID}

Thank you for your help,
    -- PlanetLab Central (%(support_email)s)
"""
	nodedown_four_subject="Server {HOSTNAME} is unreachable: Waiting Forever"
	nodedown_four=""" 
Hello,

We hope that you're having a good day.  As part of PlanetLab node monitoring, we noticed the following node is down at your site:

    {HOSTNAME} : Since {EVENT.AGE}

We have not heard a response from you regarding this machine.  We will continue sending message until we receive an acknowledgment and description of the issue prevening the node from remaining online.

You can acknowledge this notice by visiting the link below or by letting us know what the problem is by replying to this message.

    http://%(hostname)s/zabbix/acknow.php?eventid={EVENT.ID}
    http://%(hostname)s/zabbix/tr_events.php?triggerid={TRIGGER.ID}&eventid={EVENT.ID}

Thank you for your help,
    -- PlanetLab Central (%(support_email)s)
"""
	thankyou_nodeup = """
While monitoring your site, we noticed that the following nodes *improved* their states:

    {HOSTNAME} : Available

Often, system administration is a thankless job, but not today. :-)

Thank you!
  -- PlanetLab Central (%(support_email)s)
"""
