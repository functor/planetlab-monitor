#!/bin/bash

MDIR=/usr/share/monitor
source $MDIR/monitorconfig.sh
${MONITOR_SCRIPT_ROOT}/plcquery.py --type person --withsitename --byrole admin \
					--format="%(email)s,%(first_name)s %(last_name)s,%(name)s" \
				| ${MONITOR_SCRIPT_ROOT}/rt3/adduserstort.pl priv -
