import sys
import xmlrpclib
import cherrypy
import turbogears
from datetime import datetime, timedelta
import time
from monitor.wrapper import plc
import os, errno

class LocalExtensions(object):

	@cherrypy.expose()
	def example(self, **keywords):
        pass
