#!/usr/bin/python

from distutils.core import setup

packages=[	'monitor', 
			'monitor.database', 
			'monitor.Rpyc', 
			'monitor.database.zabbixapi', 
			'monitor.database.info', 
			'monitor.sources', 
			'monitor.util', 
			'monitor.wrapper' ]

print packages
setup(name='MonitorModule',
      version='2.0',
      description='Monitor Utility Module',
      author='Stephen Soltesz',
      author_email='soltesz@cs.princeton.edu',
      url='http://www.planet-lab.org',
	  packages=packages,
)

packages=['pcucontrol', 
		'pcucontrol.util',
		'pcucontrol.transports',
		'pcucontrol.transports.ssh',
		'pcucontrol.transports.pyssh',
		'pcucontrol.models',
		'pcucontrol.models.hpilo',
		'pcucontrol.models.hpilo.iloxml',
		'pcucontrol.models.intelamt',
		'pcucontrol.models.intelamt',

	]

# TODO: add data dir for intelamt and hpilo stuff
print packages
setup(name='PCUControlModule',
      version='2.0',
      description='PCU Control Module',
      author='Stephen Soltesz',
      author_email='soltesz@cs.princeton.edu',
      url='http://www.planet-lab.org',
	  packages=packages,
)

