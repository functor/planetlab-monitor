#!/bin/bash

set -e
cd $HOME/research/planetlab/svn/monitor/
source ssh.env.sh
export SSH_AUTH_SOCK
ssh -A soltesz@pl-virtual-03 "monitor/automate_pl03.sh"
