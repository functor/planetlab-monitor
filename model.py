#

import time
from datetime import datetime, timedelta
import re

class MonRecord(object):
	def __init__(self, data):
		self.keys = data.keys()
		self.keys.sort()
		self.__dict__.update(data)
		return

	def get(self):
		ret= {}
		for k in self.keys:
			ret[k] = self.__dict__[k]
		return ret

	def __repr__(self):
		str = ""
		str += self.host + "\n"
		for k in self.keys:
			if "message" in k or "msg" in k:
				continue
			if 'time' in k:
				s_time=time.strftime("%Y/%m/%d %H:%M:%S", 
							time.gmtime(self.__dict__[k]))
				str += "\t'%s' : %s\n" % (k, s_time)
			else:
				str += "\t'%s' : %s\n" % (k, self.__dict__[k])
		str += "\t--"
		return str

	def delField(self, field):
		if field in self.__dict__:
			del self.__dict__[field]
		
		if field in self.keys:
			for i in range(0,len(self.keys)):
				if self.keys[i] == field:
					del self.keys[i]
					break

class LogRoll:
	def __init__(self, list=None):
		self.list = list
		if self.list == None:
			self.list = {}

	def find(self, host, filter, timerange):
		if host not in self.list:
			return None

		host_log_list = self.list[host]
		for log in host_log_list:
			for key in filter.keys():
				#print "searching key %s in log keys" % key
				if key in log.keys:
					#print "%s in log.keys" % key
					cmp = re.compile(filter[key])
					res = cmp.search(log.__getattribute__(key))
					if res != None:
						print "found match in log: %s  %s ~=~ %s" % (log, key, filter[key])
						if log.time > time.time() - timerange:
							print "returning log b/c it occured within time."
							return log
		return None
		

	def get(self, host):
		if host in self.list:
			return self.list[host][0]
		else:
			return None

	def add(self, log):
		if log.host not in self.list:
			self.list[log.host] = []

		self.list[log.host].insert(0,log)

class Log(MonRecord):
	def __init__(self, host, data):
		self.host = host
		MonRecord.__init__(self, data)
		return

	def __repr__(self):
		str = " "
		str += self.host + " : { "
		for k in self.keys:
			if "message" in k or "msg" in k:
				continue
			if 'time' in k:
				s_time=time.strftime("%Y/%m/%d %H:%M:%S", 
							time.gmtime(self.__dict__[k]))
				#str += " '%s' : %s, " % (k, s_time)
			elif 'action' in k:
				str += "'%s' : %s, " % (k, self.__dict__[k])
		str += "}"
		return str
	

class Diagnose(MonRecord):
	def __init__(self, host):
		self.host = host
		MonRecord.__init__(self, data)
		return

class Action(MonRecord):
	def __init__(self, host, data):
		self.host = host
		MonRecord.__init__(self, data)
		return

	def deltaDays(self, delta):
		t = datetime.fromtimestamp(self.__dict__['time'])
		d = t + timedelta(delta)
		self.__dict__['time'] = time.mktime(d.timetuple())
		
	

