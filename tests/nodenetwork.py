#!/usr/bin/python

import sys
import plc
api = plc.getAuthAPI()
import util.file

if len(sys.argv[1:]) > 0:
	for host in sys.argv[1:]:
		n = api.GetNodes(host)[0]
		nn = api.GetInterfaces(n['interface_ids'])
		for nodenet in nn:
			nnet2 = api.GetInterfaces({'ip': nodenet['ip']})
			print "len of nn entries with ip: %s == %s " % ( nodenet['ip'], len(nnet2) )
			for nn2 in nnet2:
				n2 = api.GetNodes(nn2['node_id'])
				print "\t%d node is attached to nodenetwork %s" % ( len(n2), nn2['interface_id'] )
				if len(n2) != 0 :
					n2 = n2[0]
					print
					#print "host %s : %s" % (n2['hostname'], n2['node_id'])
				else:
					pass
					#print nn2['interface_id']
					#api.DeleteNodeNetwork(nn2['interface_id'])
else:
	nnids = util.file.getListFromFile('nnids.txt')
	nnids = [ int(i) for i in nnids]
	for id in nnids:
		nnet2 = api.GetInterfaces(id)
		for nn2 in nnet2:
			n2 = api.GetNodes(nn2['node_id'])
			if len(n2) == 0 :
				print "\t%d node is attached to nodenetwork %s %s" % ( len(n2), nn2['interface_id'] , nn2['ip']),

				netlist = api.GetInterfaces({'ip' : nn2['ip']})
				if len(netlist) != 1:
					node_len = len([ n['node_id'] for n in netlist])
					print "\t but, ip %s is used by %s nodenetwork entries" % (nn2['ip'], node_len)
				else:
					print
				#print nn2
			else:
				print
				pass
