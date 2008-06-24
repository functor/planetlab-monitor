#!/usr/bin/python

import sys
import plc
import auth
api = plc.PLC(auth.auth, auth.plc)
import config

if len(sys.argv[1:]) > 0:
	for host in sys.argv[1:]:
		n = api.GetNodes(host)[0]
		nn = api.GetNodeNetworks(n['nodenetwork_ids'])
		for nodenet in nn:
			nnet2 = api.GetNodeNetworks({'ip': nodenet['ip']})
			print "len of nn entries with ip: %s == %s " % ( nodenet['ip'], len(nnet2) )
			for nn2 in nnet2:
				n2 = api.GetNodes(nn2['node_id'])
				print "\t%d node is attached to nodenetwork %s" % ( len(n2), nn2['nodenetwork_id'] )
				if len(n2) != 0 :
					n2 = n2[0]
					print
					#print "host %s : %s" % (n2['hostname'], n2['node_id'])
				else:
					pass
					#print nn2['nodenetwork_id']
					#api.DeleteNodeNetwork(nn2['nodenetwork_id'])
else:
	nnids = config.getListFromFile('nnids.txt')
	nnids = [ int(i) for i in nnids]
	for id in nnids:
		nnet2 = api.GetNodeNetworks(id)
		for nn2 in nnet2:
			n2 = api.GetNodes(nn2['node_id'])
			if len(n2) == 0 :
				print "\t%d node is attached to nodenetwork %s %s" % ( len(n2), nn2['nodenetwork_id'] , nn2['ip']),

				netlist = api.GetNodeNetworks({'ip' : nn2['ip']})
				if len(netlist) != 1:
					node_len = len([ n['node_id'] for n in netlist])
					print "\t but, ip %s is used by %s nodenetwork entries" % (nn2['ip'], node_len)
				else:
					print
				#print nn2
			else:
				print
				pass
