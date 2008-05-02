#!/usr/bin/python

import os
import sys
import string
import time
import soltesz
import plc

args = {}
args['known_hosts'] = "/home/soltesz/.ssh/known_hosts"

class SSHKnownHosts:
	def __init__(self, args = args):
		self.args = args
		self.read_knownhosts()

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
		l_nodes = plc.getNodes() 
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
		node = plc.getNodes(host) 
		(host, ip, _, _) = self._record_from_node(node[0])
		index = "%s,%s" % (host,ip)
		if index in self.pl_keys:
			del self.pl_keys[index]
		if index in self.other_keys:
			del self.other_keys[index]

	def updateDirect(self, host):
		cmd = os.popen("/usr/bin/ssh-keyscan -t rsa %s 2>/dev/null" % host)
		line = cmd.read()
		(h,  ip,  key,  comment) = self._split_kh_entry(line[:-1])
		node = plc.getNodes(host)
		(host2, ip2, x, x) = self._record_from_node(node[0])
		rec = { self._get_index(host2, ip2) : "%s %s" % (key, "DIRECT") }

		self.delete(host)
		self.other_keys.update(rec)

	def update(self, host):
		node = plc.getNodes(host) 
		ret = self._record_from_node(node[0])
		(host, ip, key, comment)  = ret
		if ip == None:
			self.updateDirect(host)
		else:
			rec = { "%s,%s" % (host,ip) : "%s %s" % (key, comment) }
			self.pl_keys.update(rec)

	def _record_from_node(self, node, nokey_list=None):
		host = node['hostname']
		key = node['ssh_rsa_key']

		l_nw = plc.getNodeNetworks({'nodenetwork_id':node['nodenetwork_ids']})
		if len(l_nw) == 0:
			# No network for this node. So, skip it.
			return (host, None, None, None)

		ip = l_nw[0]['ip']

		if key == None:
			if nokey_list is not None: nokey_list += [node]
			return (host, ip, None, None)

		key = key.strip()
		# TODO: check for '==' at end of key.
		if key[-1] != '=':
			print "Host with corrupt key! for %s %s" % (node['boot_state'], node['hostname'])

		s_date = time.strftime("%Y/%m/%d_%H:%M:%S",time.gmtime(time.time()))
		#rec = { "%s,%s" % (host,ip) : "%s %s" % (key, "PlanetLab_%s" % (s_date)) }
		#return rec
		return (host, ip, key, "PlanetLab_%s" % s_date) 


def main():
	k = SSHKnownHosts()
	nokey_list = k.updateAll()

	for node in nokey_list:
		print "%5s %s" % (node['boot_state'], node['hostname'])
	
if __name__ == '__main__':
	#main()
	k = SSHKnownHosts()
	#print "update"
	#k.update('planetlab-4.cs.princeton.edu')
	#print "updateDirect"
	k.update(sys.argv[1])
	#k.updateDirect(sys.argv[1])
	k.write()
