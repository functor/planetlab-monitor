#!/bin/bash

source /usr/share/monitor/nagios/common.sh

RAW=$( random_sample /usr/share/monitor/nagios/rttickets_check_data.txt )
RUNTIME=$( echo $RAW | awk '{print $1}' )
STATE=$( echo $RAW | awk '{print $2}' )
SLEEP=`echo "scale=3; $RUNTIME * 950000" | bc`
HOST=rt.planet-lab.org
open_http $HOST

usleep $SLEEP
/usr/lib/nagios/plugins/check_dummy $( str_to_state $STATE ) "Slept $RUNTIME sec for $STATE"
R=$?

close_http
exit $R
