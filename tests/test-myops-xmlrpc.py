#!/usr/bin/python

from monitor.wrapper import plc

api = plc.getAPI("https://monitor.planet-lab.org/monitor/XMLRPC")
print api.upAndRunning()
print api.setBootmanSequence(plc.api.auth, "test-sequence", "value3")
print api.getBootmanSequences(plc.api.auth)
