#!/usr/bin/python2
#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $
from emailTxt import *
import xml, xmlrpclib
import smtplib

MTA="localhost"
FROM="support@planet-lab.org"

XMLRPC_SERVER = 'https://www.planet-lab.org/PLCAPI/'

def siteId(hostname):
	api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
	anon = {'AuthMethod': "anonymous"}
	site_id = api.AnonAdmQuerySite (anon, {"node_hostname": hostname})
	if len(site_id) == 1:  
		loginbase = api.AnonAdmGetSites (anon, site_id, ["login_base"])
		return loginbase[0]['login_base']


def slices(loginbase):
        api = xmlrpclib.Server(XMLRPC_SERVER, verbose=False)
        return api.SliceListNames (auth.auth, loginbase)


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
   	server = smtplib.SMTP(MTA)
   	server.sendmail(FROM, to,  msg)
	server.quit()

if __name__=="__main__":
	import smtplib
	import emailTxt
	id = siteId("alice.cs.princeton.edu")
	print id
	#if id:
   		#email('TEST', emailTxt.mailtxt.ssh % {'hostname': "ALICE.cs.princeton.edu"}, "tech-" + id + "@sites.planet-lab.org")
	#else:
	#	print "No dice."
	#email("TEST109", "THIS IS A TEST", ["faiyaza@cs.princeton.edu", "faiyaz@winlab.rutgers.edu", "faiyaza@gmail.com"])
