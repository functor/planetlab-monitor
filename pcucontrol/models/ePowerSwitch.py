from pcucontrol.reboot import *

class ePowerSwitchNew(PCUControl):
	supported_ports = [80]
	# NOTE:
	# 		The old code used Python's HTTPPasswordMgrWithDefaultRealm()
	#		For some reason this both doesn't work and in some cases, actually
	#		hangs the PCU.  Definitely not what we want.
	#		
	# 		The code below is much simpler.  Just letting things fail first,
	# 		and then, trying again with authentication string in the header.
	#		
	def run_http(self, node_port, dryrun):
		self.transport = None
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		req = urllib2.Request(self.url)
		try:
			handle = urllib2.urlopen(req)
		except IOError, e:
			# NOTE: this is expected to fail initially
			pass
		else:
			print self.url
			print "-----------"
			print handle.read()
			print "-----------"
			return "ERROR: not protected by HTTP authentication"

		if not hasattr(e, 'code') or e.code != 401:
			return "ERROR: failed for: %s" % str(e)

		base64data = base64.encodestring("%s:%s" % (self.username, self.password))[:-1]
		# NOTE: assuming basic realm authentication.
		authheader = "Basic %s" % base64data
		req.add_header("Authorization", authheader)

		try:
			f = urllib2.urlopen(req)
		except IOError, e:
			# failing here means the User/passwd is wrong (hopefully)
			raise ExceptionPassword("Incorrect username/password")

		# NOTE: after verifying that the user/password is correct, 
		# 		actually reboot the given node.
		if not dryrun:
			try:
				data = urllib.urlencode({'P%d' % node_port : "r"})
				req = urllib2.Request(self.url + "cmd.html")
				req.add_header("Authorization", authheader)
				# add data to handler,
				f = urllib2.urlopen(req, data)
				#if self.transport.verbose: print f.read()
			except:
				import traceback; traceback.print_exc()

				# fetch url one more time on cmd.html, econtrol.html or whatever.
				# pass
		else:
			#if self.transport.verbose: print f.read()
			pass

		return 0

class ePowerSwitchOld(PCUControl):
	def run_http(self, node_port, dryrun):
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		# create authinfo
		authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
		authinfo.add_password (None, uri, self.username, self.password)
		authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

		# NOTE: it doesn't seem to matter whether this authinfo is here or not.
		transport = urllib2.build_opener(authinfo)
		f = transport.open(self.url)
		if self.transport.verbose: print f.read()

		if not dryrun:
			transport = urllib2.build_opener(authhandler)
			f = transport.open(self.url + "cmd.html", "P%d=r" % node_port)
			if self.transport.verbose: print f.read()

		self.transport.close()
		return 0

class ePowerSwitchOld(PCUControl):
	supported_ports = [80]
	def run_http(self, node_port, dryrun):
		self.url = "http://%s:%d/" % (self.host,80)
		uri = "%s:%d" % (self.host,80)

		# TODO: I'm still not sure what the deal is here.
		# 		two independent calls appear to need to be made before the
		# 		reboot will succeed.  It doesn't seem to be possible to do
		# 		this with a single call.  I have no idea why.

		# create authinfo
		authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
		authinfo.add_password (None, uri, self.username, self.password)
		authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

		# NOTE: it doesn't seem to matter whether this authinfo is here or not.
		transport = urllib2.build_opener()
		f = transport.open(self.url + "elogin.html", "pwd=%s" % self.password)
		if self.transport.verbose: print f.read()

		if not dryrun:
			transport = urllib2.build_opener(authhandler)
			f = transport.open(self.url + "econtrol.html", "P%d=r" % node_port)
			if self.transport.verbose: print f.read()

		#	data= "P%d=r" % node_port
		#self.open(self.host, self.username, self.password)
		#self.sendHTTP("elogin.html", "pwd=%s" % self.password)
		#self.sendHTTP("econtrol.html", data)
		#self.sendHTTP("cmd.html", data)

		#self.close()
		return 0
