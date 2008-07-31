#!/bin/bash

if [ -z "$1" ] ; then
	echo "getting pid list"
	l=`ps ax | grep automate | grep -v grep | awk '{print $1}'`
else
	l=$1
fi

for pid  in $l ; do 
	pstree -p -a -A $pid | awk -F ',' '{print $2}' | \
		awk '{print $1}' | tr ')' ' ' | xargs kill  || :
done 
