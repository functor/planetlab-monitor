
class NagiosObject(object):
	trans = {'d2_coords': '2d_coords'}

	def __init__(self, id, **kwargs):
		self.id = id
		self.kwords = kwargs.keys()
		for key in self.kwords:
			self.__setattr__(key, kwargs[key])

	def toString(self):
		ret = ""
		ret += "define %s {\n" % self.id
		for key in self.kwords:
			if key in self.trans:
				ret += "    %s   %s\n" % (self.trans[key], self.__getattribute__(key))
			else:
				ret += "    %s   %s\n" % (key, self.__getattribute__(key))
		ret += "}\n"
		return ret

class Command(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "command", **kwargs)

class Host(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "host", **kwargs)

class HostGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "hostgroup", **kwargs)

class HostEscalation(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "hostescalation", **kwargs)

class Contact(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "contact", **kwargs)

class ContactGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "contactgroup", **kwargs)

class Service(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "service", **kwargs)

class ServiceDependency(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicedependency", **kwargs)

class ServiceEscalation(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "serviceescalation", **kwargs)

class ServiceGroup(NagiosObject):
	def __init__(self, **kwargs):	
		NagiosObject.__init__(self, "servicegroup", **kwargs)
