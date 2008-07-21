#!/usr/bin/python

import auth
import plc
import sys
import os

def getconf(hostname, force=False, media=None):
	api = plc.PLC(auth.auth, auth.plc)
	n = api.GetNodes(hostname)
	filename = "bootcd-alpha/" + hostname + ".txt"
	if not os.path.exists(filename) or force:
		f = open("bootcd-alpha/" + hostname + ".txt", 'w')
		f.write( api.AdmGenerateNodeConfFile(n[0]['node_id']) )
		f.close()
		print os.system("cd bootcd-alpha; ./build.sh -f %s.txt -t iso -o /plc/data/var/www/html/bootcds/%s.iso &> /dev/null" % ( hostname, hostname))
		print os.system("cd bootcd-alpha; ./build.sh -f %s.txt -t usb_partition -o /plc/data/var/www/html/bootcds/%s-partition.usb &> /dev/null" % ( hostname, hostname))
	else:
		# assume that the images have already been generated..
		pass

	args = {}
	if not media:
		args['url_list']  = "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s-partition.usb\n" % hostname
		args['url_list'] += "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s.iso" % hostname
	else:
		if media == "usb":
			args['url_list']  = "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s-partition.usb\n" % hostname
		elif media == "iso":
			args['url_list']  = "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s.iso" % hostname
		else:
			args['url_list']  = "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s-partition.usb\n" % hostname
			args['url_list'] += "   http://pl-virtual-03.cs.princeton.edu/bootcds/%s.iso" % hostname
			
	#print "http://pl-virtual-03.cs.princeton.edu/bootcds/%s.usb\n" % hostname

	return args

if __name__ == '__main__':
	from config import config as cfg
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(media='both', force=False)
	parser.add_option("", "--media", dest="media", metavar="usb, iso, both", 
						help="""Which media to generate the message for.""")
	parser.add_option("", "--force", dest="force", action="store_true", 
						help="""Force the recreation of the usb images.""")

	config = cfg(parser)
	config.parse_args()

	ret = {'url_list' : ''} 
	for i in config.args:
		conf = getconf(i, config.force, config.media)
		ret['url_list'] += conf['url_list']
		ret['hostname'] = i

	if config.media == "both":
		print """
Hello,

Here are links to both the ISO CD image, and partitioned, USB image for the
DC7800 and others.  These are based on the new 4.2 BootImage, and are the most
up-to-date software for PlanetLab nodes.

%(url_list)s

All that is necessary is to raw-write these images to a usb stick or CD-ROM, and
then boot from them.  If using USB, please use a command like:

   dd if=%(hostname)s.usb of=/dev/sdX

Where sdX is your USB device.  It is not necessary to run any other formatting
commands for these images, because they already include a MBR, partition
table, and fs.

Please let me know if you have any trouble.

Thank you,

""" % ret

	elif config.media == "iso":
		print """
Hello,

Here are links to the ISO CD image(s) for your machines.  These are based on
the new 4.2 BootImage, and are the most up-to-date software for PlanetLab
nodes.

%(url_list)s

All that is necessary is to burn these images to a CD-ROM, and
then boot from them.  

Please let me know if you have any trouble.

Thank you,

""" % ret

	elif config.media == "usb":
		print """
Hello,

Here are links to the partitioned, USB images for the DC7800 and others.  
These are based on the new 4.2 BootImage, and are the most
up-to-date software for PlanetLab nodes.

%(url_list)s

All that is necessary is to raw-write these images to a usb stick, and
then boot from them.  Please use a command like:

   dd if=%(hostname)s.usb of=/dev/sdX

Where sdX is your direct, USB device.  Do not use a partition on the usb
image, or the boot will fail.  It is not necessary to run any other formatting
commands for these images, because they already include a MBR, partition
table, and fs.

Please let me know if you have any trouble.

Thank you,

""" % ret
