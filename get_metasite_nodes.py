#!/usr/bin/python
import plc
import soltesz
import string
import sys

def main():
	meta_sites = ['canarie', 'rnp', 'jgn2', 'i2', 'tp', 'princeton', 'princetondsl', 'plcolo', 'wide']
	l_blacklist = [ "grouse.hpl.hp.com", "planet1.att.nodes.planet-lab.org"]
	#l_blacklist = soltesz.dbLoad("l_blacklist")
	l_sitelist = []
	count = 0
	# for each prefix above
	for pre_loginbase in meta_sites:
		print "getting sites from base %s*" % pre_loginbase
		search_sites  = plc.getSites({'login_base' : pre_loginbase + "*"})
		# for each of the sites that begin with this prefix
		for site in search_sites:
			# get the nodes for that site
			l_sitelist.append(site['login_base'])
			print "%s : " % site['login_base']
			nodes = plc.getSiteNodes2(site['login_base'])
			for node in nodes:
				hn = node['hostname']
				if hn not in l_blacklist:
					print "\t%s" % hn
					count += 1
					# add the nodes to the blacklist
					l_blacklist.append(hn)
				#else:
				#	print "not adding %s" % hn
	print string.join(l_sitelist,  ",")
	print "Found %d nodes" % count
	print "Found %d sites " % len(l_sitelist)

	soltesz.dbDump("l_blacklist")

if __name__=="__main__":
	main() 
