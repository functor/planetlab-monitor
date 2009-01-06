from pcucontrol.reboot import *

### rebooting european BlackBox PSE boxes
# Thierry Parmentelat - May 11 2005
# tested on 4-ports models known as PSE505-FR
# uses http to POST a data 'P<port>=r'
# relies on basic authentication within http1.0
# first curl-based script was
# curl --http1.0 --basic --user <username>:<password> --data P<port>=r \
#	http://<hostname>:<http_port>/cmd.html && echo OK

# log in:

## BB PSMaverick
class BlackBoxPSMaverick(PCUControl):
	supported_ports = [80]

	def run_http(self, node_port, dryrun):
		if not dryrun:
			# send reboot signal.
			cmd = "curl -s --data 'P%s=r' --anyauth --user '%s:%s' http://%s/config/home_f.html" % ( node_port, self.username, self.password, self.host)
		else:
			# else, just try to log in
			cmd = "curl -s --anyauth --user '%s:%s' http://%s/config/home_f.html" % ( self.username, self.password, self.host)

		p = os.popen(cmd)
		result = p.read()
		print "RESULT: ", result

		if len(result.split()) > 3:
			return 0
		else:
			return result

def bbpse_reboot (pcu_ip,username,password,port_in_pcu,http_port, dryrun):

	global verbose

	url = "http://%s:%d/cmd.html" % (pcu_ip,http_port)
	data= "P%d=r" % port_in_pcu
	if verbose:
		logger.debug("POSTing '%s' on %s" % (data,url))

	authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
	uri = "%s:%d" % (pcu_ip,http_port)
	authinfo.add_password (None, uri, username, password)
	authhandler = urllib2.HTTPBasicAuthHandler( authinfo )

	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)

	if (dryrun):
		return 0

	try:
		f = urllib2.urlopen(url,data)

		r= f.read()
		if verbose:
			logger.debug(r)
		return 0

	except urllib2.URLError,err:
		logger.info('Could not open http connection', err)
		return "bbpse error"
