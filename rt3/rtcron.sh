#!/bin/bash

D=/usr/share/monitor/
for f in $D/rt3/rtcron.d/*.sh ; do
	bash -c "$f"
done
