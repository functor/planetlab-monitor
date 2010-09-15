#!/bin/bash

NODES="1280 640 320"
TIMES="7 15 30 60 120"

D=`date +%s`

# NOTE: we should only need to do this once.  Every restart will inherit the
#       last retention file after restarting.

function block_until_hour ()
{
    d=`date +%s`
    last_hour=$(( $d - $d % (60 * 60 ) ))
    next_hour=$(( $last_hour + 60*60 ))
    while [ $next_hour -gt `date +%s` ] ; do 
        sleep 10
    done
}

#block_until_hour
cp /usr/share/monitor/nagios/retention.dat /var/log/nagios/retention.dat 

echo "Restoring complete retention.dat"
echo "START time nodes start"
for N in $NODES ; do 
    cp /var/log/nagios/retention.dat /tmp/retention.dat 
    /usr/share/monitor/nagios/filter_nagios_retention.py 7 1280 /tmp/retention.dat > /var/log/nagios/retention.dat

    for T in $TIMES ; do 
        service nagios stop
        echo "Generating plcnodes with $T min intervals & $N nodes"
        ./plc_test_hosts.py $T $N > /etc/nagios/objects/plcnodes.cfg
        echo "Sleeping before starting nagios"
        block_until_hour
        D=`date +%s`
        echo "START $T $N" $D $(( $D + 60*60 )) >> stimes.txt
        service nagios start
        sleep $(( 50*60 ))
    done
done


service nagios stop
sleep $(( 10*60 ))
cp /etc/nagios/objects/plc.cfg /etc/nagios/objects/plcnodes.cfg
service nagios start

