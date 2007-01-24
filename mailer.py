#!/usr/bin/python2
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: mailer.py,v 1.5 2007/01/17 16:03:30 faiyaza Exp $
from emailTxt import *
import smtplib
import config

MTA="localhost"
FROM="support@planet-lab.org"

def email (subject, text, to):
	"""Create a mime-message that will render HTML in popular
	MUAs, text in better ones"""
	import MimeWriter
	import mimetools
	import cStringIO

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
		writer.addheader("CC", cc)
	else:
		writer.addheader("To", to)
		
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
	if not config.debug:
		try:
   			server = smtplib.SMTP(MTA)
   			server.sendmail(FROM, to,  msg)
			server.quit()
		except Exception, err:
			print "Mailer error: %s" % err

if __name__=="__main__":
	import smtplib
	import emailTxt
	import plc 
	id = plc.siteId(["alice.cs.princeton.edu"])
	print id
	#if id:
   		#email('TEST', emailTxt.mailtxt.ssh % {'hostname': "ALICE.cs.princeton.edu"}, "tech-" + id + "@sites.planet-lab.org")
	#else:
	#	print "No dice."
	#email("TEST109", "THIS IS A TEST", ["faiyaza@cs.princeton.edu", "faiyaz@winlab.rutgers.edu", "faiyaza@gmail.com"])
