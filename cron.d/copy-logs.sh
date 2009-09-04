#!/bin/bash

cd /usr/share/monitor
source agent.sh &> /dev/null

rsync -qv -az -e ssh root@chloe.cs.princeton.edu:/vservers/www-current/var/log/httpd/*-* /var/lib/monitor/httpd-log
rsync -qv -az -e ssh root@chloe.cs.princeton.edu:/vservers/www-current/var/log/httpd/*error* /var/lib/monitor/httpd-log

rsync -qv -az -e ssh root@chloe.cs.princeton.edu:/vservers/www-current/var/log/*-filesystem* /var/lib/monitor/filesystem
rsync -qv -az -e ssh root@chloe.cs.princeton.edu:/vservers/www-current/var/log/*-checkrpm* /var/lib/monitor/checkrpm

rsync -qv -az -e ssh root@amber.cs.princeton.edu:/vservers/db-current/var/log/*-filesystem* /var/lib/monitor/filesystem
rsync -qv -az -e ssh root@amber.cs.princeton.edu:/vservers/db-current/var/log/*-checkrpm* /var/lib/monitor/checkrpm

rsync -qv -az -e ssh root@janine.cs.princeton.edu:/vservers/boot-current/var/log/*-filesystem* /var/lib/monitor/filesystem
rsync -qv -az -e ssh root@janine.cs.princeton.edu:/vservers/boot-current/var/log/*-checkrpm* /var/lib/monitor/checkrpm
rsync -qv -az -e ssh root@janine.cs.princeton.edu:/vservers/boot-current/var/log/bm/ /var/lib/monitor/bmlogs/
