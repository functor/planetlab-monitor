#!/usr/bin/python

import os
import sys
import string
import time
import xml, xmlrpclib
try:
	from monitor import config
	auth = {'Username'   : config.API_AUTH_USER,
	        'AuthMethod' : "password",
			'AuthString' : config.API_AUTH_PASSWORD}
except:
	import traceback
	print traceback.print_exc()
	auth = {'AuthMethod' : "anonymous"}

args = {}
args['known_hosts'] =  os.environ['HOME'] + os.sep + ".ssh" + os.sep + "known_hosts"
args['XMLRPC_SERVER'] = 'https://boot.planet-lab.org/PLCAPI/'

class SSHKnownHosts:
	def __init__(self, args = args):
		self.args = args
		self.read_knownhosts()
		self.auth = auth
		self.api = xmlrpclib.Server(args['XMLRPC_SERVER'], verbose=False, allow_none=True)
		self.nodenetworks = {}

	def _split_kh_entry(self, line):
		s = line.split(' ')
		try:
			(host,ip) = s[0].split(',')
		except:
			ip = s[0]
			host = ""

		key = ' '.join(s[1:3])
		comment = ' '.join(s[3:])
		return (host, ip, key, comment)

	def _get_index(self, host, ip):
		index = ""
		if host is not "":
			index = "%s,%s" % (host,ip)
		else:
			index = ip
		return index
		
	def read_knownhosts(self):
		kh_read = open(self.args["known_hosts"], 'r')
		self.pl_keys = {}
		self.other_keys = {}
		for line in kh_read:
			(host, ip, key, comment) = self._split_kh_entry(line[:-1])
			rec = { self._get_index(host, ip) : "%s %s" % (key, comment) }
			if 'PlanetLab' in comment:
				self.pl_keys.update(rec)
			else:
				self.other_keys.update(rec)

		#for i in self.pl_keys:
		#	print i
		#	print self.pl_keys[i]

		return

	def write(self):
		self.write_knownhosts()

	def write_knownhosts(self):
		f = open(self.args['known_hosts'], 'w')
		for index in self.pl_keys:
			print >>f, "%s %s" % (index, self.pl_keys[index])
		for index in self.other_keys:
			print >>f, "%s %s" % (index, self.other_keys[index])
		f.close()

	def updateAll(self):
		l_nodes = self.getNodes() 
		d_nodes = {}
		nokey_list = []
		for node in l_nodes:
			name = node['hostname']
			d_nodes[name] = node

		for host in d_nodes:
			node = d_nodes[host]
			(host, ip, key, comment) = self._record_from_node(node, nokey_list)
			rec = { "%s,%s" % (host,ip) : "%s %s" % (key, comment) }
			self.pl_keys.update(rec)

		return nokey_list

	def delete(self, host):
		node = self.getNodes(host) 
		if len(node) > 0:
			(host, ip, _, _) = self._record_from_node(node[0])
			index = "%s,%s" % (host,ip)
			if index in self.pl_keys:
				del self.pl_keys[index]
			if index in self.other_keys:
				del self.other_keys[index]
		return node

	def updateDirect(self, host):
		cmd = os.popen("/usr/bin/ssh-keyscan -t rsa %s 2>/dev/null" % host)
		line = cmd.read()
		(h,  ip,  key,  comment) = self._split_kh_entry(line[:-1])
		node = self.getNodes(host)
		(host2, ip2, x, x) = self._record_from_node(node[0])
		rec = { self._get_index(host2, ip2) : "%s %s" % (key, "DIRECT") }

		self.delete(host)
		self.other_keys.update(rec)

	def update(self, host):
		node = self.delete(host)
		#node = self.getNodes(host) 
		if node is not []:
			ret = self._record_from_node(node[0])
			(host, ip, key, comment)  = ret
			if ip == None:
				self.updateDirect(host)
			else:
				rec = { "%s,%s" % (host,ip) : "%s %s" % (key, comment) }
				self.pl_keys.update(rec)

	def getNodes(self, host=None):
		if type(host) == type(""): host = [host]

		# get the node(s) info
		nodes = self.api.GetNodes(self.auth,host,["hostname","ssh_rsa_key","nodenetwork_ids"])

		# for each node's node network, update the self.nodenetworks cache
		nodenetworks = []
		for node in nodes:
			for net in node["nodenetwork_ids"]:
				nodenetworks.append(net)

		plcnodenetworks = self.api.GetNodeNetworks(self.auth,nodenetworks,["nodenetwork_id","ip"])
		for n in plcnodenetworks:
			self.nodenetworks[n["nodenetwork_id"]]=n
		return nodes

	def _record_from_node(self, node, nokey_list=None):
		host = node['hostname']
		key = node['ssh_rsa_key']

		nodenetworks = node['nodenetwork_ids']
		if len(nodenetworks)==0: return (host, None, None, None)

		# the [0] subscript to node['nodenetwork_ids'] means
		# that this function wont work with multihomed nodes
		l_nw = self.nodenetworks.get(nodenetworks[0],None)
		if l_nw is None: return (host, None, None, None)
		ip = l_nw['ip']

		if key == None:
			if nokey_list is not None: nokey_list += [node]
			return (host, ip, None, None)

		key = key.strip()
		# TODO: check for '==' at end of key.
		if len(key) > 0 and key[-1] != '=':
			print "Host with corrupt key! for %s %s" % (node['boot_state'], node['hostname'])

		s_date = time.strftime("%Y/%m/%d_%H:%M:%S",time.gmtime(time.time()))
		#rec = { "%s,%s" % (host,ip) : "%s %s" % (key, "PlanetLab_%s" % (s_date)) }
		#return rec
		return (host, ip, key, "PlanetLab_%s" % s_date) 


def main(hosts):
	k = SSHKnownHosts()
	if len (hosts) > 0:
		for host in hosts:
			k.updateDirect(host)
	else:
		k.updateAll()
	k.write()

if __name__ == '__main__':
	main(sys.argv[1:])
