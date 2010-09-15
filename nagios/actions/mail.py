#!/usr/bin/python

import time
import sys
import os

host_msg = """***** MyOpsNagios %(hostnotificationnumber)s *****
        
Notification Type: %(notificationtype)s

Host: %(hostname)s
State: %(hoststate)s
Address: %(hostaddress)s
Info: %(hostoutput)s

Date/Time: %(longdatetime)s"""

service_msg = """***** MyOpsNagios %(servicenotificationnumber)s %(hostnotificationnumber)s *****

Notification Type: %(notificationtype)s

Service: %(servicedesc)s
Host: %(hostalias)s
Address: %(hostaddress)s
State: %(servicestate)s

Date/Time: %(longdatetime)s

Additional Info:

    http://pl-service-04.cs.princeton.edu/nagios/cgi-bin/trends.cgi?host=%(hostalias)s&service=%(servicedesc)s
    http://pl-service-04.cs.princeton.edu/nagios/cgi-bin//status.cgi?hostgroup=%(hostalias)s&style=detail

%(serviceoutput)s"""


def argv_to_dict(argv):
    """
        NOTE: very bare-bones, no error checking, will fail easily.
    """
    d = {}
    prev=None
    for a in argv:
        if "--" in a:
            prev = a[2:]
        else:
            d[prev] = a
    return d

if __name__ == '__main__':
    f = open("/tmp/myopsmail", 'a')
    f.write("mail %s %s\n" % (time.time(), " ".join(sys.argv[1:])))
    f.close()

    d = argv_to_dict(sys.argv[1:])
    #print d.keys()
    if 'host' in d:

        msg = host_msg % d
        subject = """ "** %(notificationtype)s Host Alert: %(hostname)s is %(hoststate)s **" """ % d
    else:

        msg = service_msg % d
        if 'contactgroupname' in d:
            subject = """ "** %(notificationtype)s Service Alert: %(contactgroupname)s %(hostalias)s/%(servicedesc)s is %(servicestate)s **" """ % d
        else:
            subject = """ "** %(notificationtype)s Service Alert: %(hostalias)s/%(servicedesc)s is %(servicestate)s **" """ % d



    f = os.popen("""/bin/mail -S replyto=monitor@planet-lab.org -s %s %s""" % (subject, d['contactemail']), 'w')
    f.write(msg)


#        command_line="""/usr/bin/printf "%%b" "***** MyOpsNagios %(hostnotificationnumber)s *****\\n\\nNotification Type: %(notificationtype)s\\nHost: %(hostname)s\\nState: %(hoststate)s\\nAddress: %(hostaddress)s\\nInfo: %(hostoutput)s\\n\\nDate/Time: %(longdatetime)s\\n" | /bin/mail -S replyto=monitor@planet-lab.org -s "** %(notificationtype)s Host Alert: %(hostname)s is %(hoststate)s **" %(contactemail)s""" % d
        #command_line="""/usr/bin/printf "%%b" "***** MyOpsNagios %(servicenotificationnumber)s %(hostnotificationnumber)s *****\\n\\nNotification Type: %(notificationtype)s\\n\\nService: %(servicedesc)s\\nHost: %(hostalias)s\\nAddress: %(hostaddress)s\\nState: %(servicestate)s\\n\\nDate/Time: %(longdatetime)s\\n\\nAdditional Info:\\n\\n%(serviceoutput)s" | /bin/mail -S replyto=monitor@planet-lab.org -s "** %(notificationtype)s Service Alert: %(hostalias)s/%(servicedesc)s is %(servicestate)s **" %(contactemail)s""" % d
    #os.system(command_line)


