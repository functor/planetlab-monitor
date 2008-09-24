#!/usr/bin/python

import plc
api = plc.getAuthAPI()
import sys
import os
import config

def getconf(hostname, force=False, media=None):
	n = api.GetNodes(hostname)
	filename = "bootcd/" + hostname + ".txt"
	if not os.path.exists(filename) or force:
		f = open("bootcd/" + hostname + ".txt", 'w')
		f.write( api.AdmGenerateNodeConfFile(n[0]['node_id']) )
		f.close()
		print os.system("cd bootcd; ./build.sh -f %s.txt -t iso -o /plc/data/var/www/html/bootcds/%s.iso &> /dev/null" % ( hostname, hostname))
		print os.system("cd bootcd; ./build.sh -f %s.txt -t usb_partition -o /plc/data/var/www/html/bootcds/%s-partition.usb &> /dev/null" % ( hostname, hostname))
	else:
		# assume that the images have already been generated..
		pass

	args = {}
	if not media:
		args['url_list']  = "   http://%s/bootcds/%s-partition.usb\n" % (config.MONITOR_HOSTNAME, hostname)
		args['url_list'] += "   http://%s/bootcds/%s.iso" % (config.MONITOR_HOSTNAME, hostname)
	else:
		if media == "usb":
			args['url_list']  = "   http://%s/bootcds/%s-partition.usb\n" % (config.MONITOR_HOSTNAME, hostname)
		elif media == "iso":
			args['url_list']  = "   http://%s/bootcds/%s.iso" % (config.MONITOR_HOSTNAME, hostname)
		else:
			args['url_list']  = "   http://%s/bootcds/%s-partition.usb\n" % (config.MONITOR_HOSTNAME, hostname)
			args['url_list'] += "   http://%s/bootcds/%s.iso" % (config.MONITOR_HOSTNAME, hostname)
			

	return args

if __name__ == '__main__':
	import parser as parsermodule

	parser = parsermodule.getParser()
	parser.set_defaults(media='both', force=False)
	parser.add_option("", "--media", dest="media", metavar="usb, iso, both", 
						help="""Which media to generate the message for.""")
	parser.add_option("", "--force", dest="force", action="store_true", 
						help="""Force the recreation of the usb images.""")
	parser = parsermodule.getParser(['defaults'], parser)

	config = parsesrmodule.parse_args(parser)

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
