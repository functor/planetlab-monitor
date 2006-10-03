#!/usr/bin/python
#
# Utility functions
#
# Mark Huang <mlhuang@cs.princeton.edu>
# Copyright (C) 2006 The Trustees of Princeton University
#
# $Id: pl_mom.py,v 1.4 2006/06/02 04:00:00 mlhuang Exp $
#

import os
import sys

def writepid(prog):
    """
    Check PID file. Exit if already running. Update PID file.
    """

    try:
        pidfile = file("/var/run/%s.pid" % prog, "r")
        pid = pidfile.readline().strip()
        pidfile.close()
        if os.path.isdir("/proc/" + pid):
            print "Error: Another copy of %s is still running (%s)" % (prog, pid)
            sys.exit(1)
    except IOError:
        pass

    pidfile = file("/var/run/%s.pid" % prog, "w")
    pidfile.write(str(os.getpid()))
    pidfile.close()


def removepid(prog):
    os.unlink("/var/run/%s.pid" % prog)


def daemonize():
    """
    Daemonize self. Detach from terminal, close all open files, and fork twice.
    """

    pid = os.fork()
    if pid == 0:
        # Detach from terminal
        os.setsid()
        # Orphan myself
        pid = os.fork()
        if pid == 0:
            os.chdir("/")
        else:
            os._exit(0)
    else:
        os._exit(0)

    # Close all open file descriptors
    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = 1024
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass

    # Redirect stdin to /dev/null
    os.open("/dev/null", os.O_RDWR)
