#!/usr/bin/python2
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: mailer.py,v 1.7 2007/04/06 16:16:53 faiyaza Exp $
from emailTxt import *
import smtplib
from config import config
import logging

config = config()
logger = logging.getLogger("monitor")

MTA="localhost"
FROM="monitor@planet-lab.org"

def email(subject, text, to):
	"""Create a mime-message that will render HTML in popular
	MUAs, text in better ones"""
	import MimeWriter
	import mimetools
	import cStringIO

	if config.mail and config.debug:
   		to = [config.email]

	out = cStringIO.StringIO() # output buffer for our message 
	txtin = cStringIO.StringIO(text)

	writer = MimeWriter.MimeWriter(out)
	#
	# set up some basic headers... we put subject here
	# because smtplib.sendmail expects it to be in the
	# message body
	#
	writer.addheader("Subject", subject)
	if to.__class__ == [].__class__ :	
		writer.addheader("To", to[0])
		cc = ""
		for dest in to[1:len(to)]:
			cc +="%s, " % dest
		cc = cc.rstrip(", ") 
		writer.addheader("Cc", cc)
	else:
		writer.addheader("To", to)

	if config.bcc:
		print "Adding bcc"
		writer.addheader("Bcc", config.email)

	writer.addheader("Reply-To", 'monitor@planet-lab.org')
		
	writer.addheader("MIME-Version", "1.0")
	#
	# start the multipart section of the message
	# multipart/alternative seems to work better
	# on some MUAs than multipart/mixed
	#
	writer.startmultipartbody("alternative")
	writer.flushheaders()
	#
	# the plain text section
	#
	subpart = writer.nextpart()
	subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
	pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
	mimetools.encode(txtin, pout, 'quoted-printable')
	txtin.close()
	#
	# Now that we're done, close our writer and
	# return the message body
	#
	writer.lastpart()
	msg = out.getvalue()
	out.close()
	# three cases:
	# 	mail but no-debug
	#	mail and debug, 'to' changed at the beginning'
	#   nomail, but report who I'd send to.
	if config.mail:
		try:
			# This is normal operation
			server = smtplib.SMTP(MTA)
			server.sendmail(FROM, to,  msg)
			server.quit()
		except Exception, err:
			print "Mailer error: %s" % err
	else:
		#print "Would mail %s" %to
		logger.debug("Would send mail to %s" % to)

if __name__=="__main__":
	import smtplib
	import emailTxt
	import plc 
	email("[spam] This is a mail-test from golf.cs.princeton.edu", 
		  "I'm concerned that emails aren't leaving golf.  Sorry for the spam", 
		  "princetondsl@sites.planet-lab.org")
	#id = plc.siteId(["alice.cs.princeton.edu"])
	#print id
	#if id:
   		#email('TEST', emailTxt.mailtxt.ssh % {'hostname': "ALICE.cs.princeton.edu"}, "tech-" + id + "@sites.planet-lab.org")
	#else:
	#	print "No dice."
	#email("TEST111", "I'd like to see if this works anywhere", ["soltesz@cs.princeton.edu", "soltesz@cs.utk.edu"])
	#print "mailer does nothing in main()"
