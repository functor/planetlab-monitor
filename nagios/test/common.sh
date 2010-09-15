#!/bin/bash 

function percent_true ()
{
    PERCENT=$1

    # If R is uniformly random, then it will be less than a threshold PERCENT of the time.
    P=$(( $PERCENT * 32786 / 100 ))
    R=$RANDOM

    if [ $R -gt $P ] ; then
        echo "2"
    else
        echo "0"
    fi
}

function random_delay ()
{
    MAX=$1

    R=$RANDOM
    P=$(( $R * $MAX / 32786 ))

    echo $P
}

function random_sample ()
{
    file=$1
    length=$(wc -l $file | awk '{print $1}')
    R=$RANDOM
    R_MAX=32786
    index=$(( $R * $length / $R_MAX ))

    V=`tail -$(( $length - $index )) $file  | head -1`
    echo $V
}

function str_to_state ()
{
    case "$1" in
        "OK:")
            echo "0"
            ;;
        "WARNING:")
            echo "1"
            ;;
        *)
            echo "2"
            ;;
    esac
}

function open_http ()
{
    exec 3<> /dev/tcp/$1/80
    echo "GET /index.html HTTP/1.0" 1>&3
}

function close_http ()
{
    echo 1>&3
    while read 0<&3; do echo $REPLY >/dev/null; done
}

