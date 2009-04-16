# $Id$
CURL	:= curl -H Pragma: -O -R -S --fail --show-error
SHA1SUM	= sha1sum

# default - overridden by the build
SPECFILE = zabbix.spec

#main.URL	:= http://voxel.dl.sourceforge.net/sourceforge/zabbix/zabbix-1.6.1.tar.gz 
#main.SHA1SUM	:= 6e66efdbbdf23dc3de01379b30ded7b005fb49d9
#main.URL	:= http://superb-east.dl.sourceforge.net/sourceforge/zabbix/zabbix-1.6.2.tar.gz
#main.SHA1SUM	:= 575c443adec1703c2c242dbf353de9dc3bb4cafb
main.URL	:= http://build.planet-lab.org/third-party/zabbix-1.6.2.tar.gz
main.SHA1SUM	:= 575c443adec1703c2c242dbf353de9dc3bb4cafb
main.FILE	:= $(notdir $(main.URL))

# Thierry - when called from within the build, PWD is /build
SOURCEFILES := $(main.FILE)

$(main.FILE): #FORCE
	@if [ ! -e "$@" ] ; then echo "$(CURL) $(main.URL)" ; $(CURL) $(main.URL) ; fi
	@if [ ! -e "$@" ] ; then echo "Could not download source file: $@ does not exist" ; exit 1 ; fi
	@if test "$$(sha1sum $@ | awk '{print $$1}')" != "$(main.SHA1SUM)" ; then \
	    echo "sha1sum of the downloaded $@ does not match the one from 'sources' file" ; \
	    echo "Local copy: $$(sha1sum $@)" ; \
	    echo "In sources: $$(grep $@ sources)" ; \
	    exit 1 ; \
	else \
	    ls -l $@ ; \
	fi

sources: $(SOURCEFILES)
.PHONY: sources

PWD=$(shell pwd)
PREPARCH ?= noarch
RPMDIRDEFS = --define "_sourcedir $(PWD)" --define "_builddir $(PWD)" --define "_srcrpmdir $(PWD)" --define "_rpmdir $(PWD)"

trees: sources
	rpmbuild $(RPMDIRDEFS) $(RPMDEFS) --nodeps -bp --target $(PREPARCH) $(SPECFILE)

srpm: sources
	rpmbuild $(RPMDIRDEFS) $(RPMDEFS) --nodeps -bs $(SPECFILE)

TARGET ?= $(shell uname -m)
rpm: sources
	rpmbuild $(RPMDIRDEFS) $(RPMDEFS) --nodeps --target $(TARGET) -bb $(SPECFILE)

clean:
	rm -f *.rpm *.tgz *.bz2 *.gz
clean:
	rm *.pyc *.dat *.log
