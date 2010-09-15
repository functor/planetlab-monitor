#!/bin/bash 

source /usr/share/monitor/nagios/common.sh

HOST=monitor.planet-lab.org 
open_http $HOST

PAUSE=$( random_delay 30 ) 
sleep $PAUSE
/usr/lib/nagios/plugins/check_dummy $( percent_true 90 ) "After $PAUSE sec pause; $1"
R=$?

close_http
exit $R
