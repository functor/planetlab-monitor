#
# Copyright (c) 2004  The Trustees of Princeton University (Trustees).
#
# Faiyaz Ahmed <faiyaza@cs.princeton.edu>
#
# $Id: $
#

DOCROOT="/home/faiyaza/public_html/"
DOC="index.html"
HEAD="
class Html:
	__init__(self,cmn):
		__self.cmn = cmn

	writeHtml(self):
		fd = open(DOCROOT + DOC, 'w')
		
