#!/usr/bin/python

from distutils.core import setup
#from setuptools import setup, find_packages

packages=['monitor', 'monitor.database', 'monitor.database.zabbixapi', 
		'monitor.database.infovacuum', 'monitor.pcu',
		'monitor.sources', 'monitor.util', 'monitor.wrapper' ]

#packages = find_packages(exclude=('Rpyc', 'www', 'ssh', 'pyssh',
#'Rpyc.Demo', 'Rpyc.Servers', 'www.HyperText'))
print packages
setup(name='MonitorModule',
      version='1.1',
      description='Monitor Utility Module',
      author='Stephen Soltesz',
      author_email='soltesz@cs.princeton.edu',
      url='http://www.planet-lab.org',
	  packages=packages,
)

