#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/monitor/trunk/monitor.spec $

%define name monitor
# keep this version in sync with monitor/monitor_version.py
%define version 3.1
%define taglevel 1

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}
%global python_sitearch	%( python -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)" )

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.bz2
License: GPL
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

Vendor: PlanetLab
Packager: PlanetLab Central <support@planet-lab.org>
Distribution: PlanetLab %{plrelease}
URL: %(echo %{url} | cut -d ' ' -f 2)


Summary: Monitor account initialization for the root image.
Group: Applications/System

%description
Monitor is a collection of secondary scripts for configuring the node polling
system, syncing the PLC db with the monitoring database, notifying users,
interacting with PCU hardware, applying penalties to sites that violate
acceptable use.

######################################## NAGIOS

%package nagios
Summary: Monitor integration with Nagios
Group: Applications/System

Requires: coreutils
Requires: passwd
Requires: gd
Requires: gd-devel
Requires: mysql
Requires: mysql-server
Requires: mysql-devel
Requires: mysql-libs
Requires: mailx
Requires: sendmail
Requires: php
Requires: httpd

Requires: cronie
Requires: nagios
Requires: nagios-common
Requires: nagios-devel
Requires: nagios-plugins-all
Requires: ndoutils
Requires: ndoutils-mysql

Requires: rt3


%description nagios
Scripts and setup necessary to integrate and monitor PLC with Nagios.
Best suited to F12 or above.

######################################## CLIENT

%package client
Summary: Monitor hooks for a PLC node
Group: Applications/System
Requires: curl
Requires: coreutils

%description client
The client scripts handle account creation inside of a node.  This will
include configuration setup for the monitoring agent running on the node.  It
will also include any cron or init scripts needed to perform this kind of
maintenance.
######################################## Server Deps
%package server-deps
Summary: Monitor hooks for the PLC server.
Group: Applications/System

Requires: python
Requires: python-setuptools-devel
Requires: python-peak-util-extremes

Requires: compat-libstdc++-296
Requires: openssh-clients
Requires: perl-libwww-perl
Requires: perl-IO-Socket-SSL 
Requires: MySQL-python
Requires: nmap
Requires: nc
Requires: rt3
Requires: traceroute

Requires: plewww-plekit
Requires: pcucontrol
Requires: TurboGears

#Requires: zabbix-client
#Requires: zabbix-gui
#Requires: zabbix-server

%description server-deps
The server side include all python modules and scripts needed to fully

######################################## Server
%package server
Summary: Monitor hooks for the PLC server.
Group: Applications/System

Requires: python

Requires: monitor-server-deps
Requires: PLCWWW >= 4.2
# NOTE: removed b/c 'distroname' gets corrupted during build process.
# Requires: bootcd-%{pldistro}-%{distroname}-%{_arch} >= 5.0

%description server
The server side include all python modules and scripts needed to fully
operation, track, and interact with any third-party monitoring software, such
as Zabbix DB.

####################################### RunlevelAgent
%package runlevelagent
summary: the RunlevelAgent that reports node runlevels
group: applications/system
requires: python

%description runlevelagent
The RunlevelAgent starts as early as possible during boot-up and production
mode to actively report the observed runlevel to PLC and update the
'last_contact' field.

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
#################### CLIENT 
#install -D -m 755 monitor-client.init $RPM_BUILD_ROOT/%{_initrddir}/monitor
#install -D -m 644 monitor.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor
install -D -m 755 tools/timeout.pl $RPM_BUILD_ROOT/usr/bin/timeout.pl


#################### SERVER
install -d $RPM_BUILD_ROOT/usr/share/%{name}
install -d $RPM_BUILD_ROOT/data/var/lib/%{name}
install -d $RPM_BUILD_ROOT/data/var/lib/%{name}/archive-pdb
install -d $RPM_BUILD_ROOT/var/lib/%{name}
install -d $RPM_BUILD_ROOT/var/lib/%{name}/archive-pdb
install -d $RPM_BUILD_ROOT/var/www/html/monitorlog/
install -d $RPM_BUILD_ROOT/etc/httpd/conf.d/
install -d $RPM_BUILD_ROOT/%{python_sitearch}/monitor

# plc.d scripts
install -D -m 644 monitor.functions $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor.functions
install -D -m 755 monitor-server.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor
install -D -m 755 zabbix/monitor-zabbix.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/zabbix

install -D -m 755 nagios/monitor-nagios.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor-nagios
install -D -m 644 nagios/monitor-nagios.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor-nagios.cron

# cron job for automated polling
install -D -m 644 monitor-server.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor-server.cron

# apache configuration
install -D -m 644 web/monitorweb-httpd.conf $RPM_BUILD_ROOT/etc/httpd/conf.d/

# we'll install monitor in site-packages install rest to
# /usr/share/monitor
rsync -a --exclude archive-pdb --exclude .cvsignore --exclude .svn --exclude CVS  \
    --exclude monitor/ \
    ./  $RPM_BUILD_ROOT/usr/share/%{name}/

# install monitor python package
rsync -a --exclude .svn  ./monitor/   $RPM_BUILD_ROOT/%{python_sitearch}/monitor/

install -D -m 644 monitor/wrapper/plc.py $RPM_BUILD_ROOT/usr/share/%{name}/nagios/
install -D -m 644 monitor/generic.py $RPM_BUILD_ROOT/usr/share/%{name}/nagios/

# install third-party module to site-packages
install -D -m 755 threadpool.py $RPM_BUILD_ROOT/%{python_sitearch}/threadpool.py

# TODO: 
#touch $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php
#chmod 777 $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php

#install -D -m 755 monitor-default.conf $RPM_BUILD_ROOT/etc/monitor.conf
#cp $RPM_BUILD_ROOT/usr/share/%{name}/monitorconfig-default.py $RPM_BUILD_ROOT/usr/share/%{name}/monitorconfig.py

#################### RunlevelAgent
install -D -m 755 RunlevelAgent.py $RPM_BUILD_ROOT/usr/bin/RunlevelAgent.py
install -D -m 755 monitor-runlevelagent.init $RPM_BUILD_ROOT/%{_initrddir}/monitor-runlevelagent

mkdir -p $RPM_BUILD_ROOT/var/log
touch $RPM_BUILD_ROOT/var/log/server-deps.log


%clean
rm -rf $RPM_BUILD_ROOT

%files server-deps
/var/log/server-deps.log

%files nagios
%defattr(-,root,root)
%{_sysconfdir}/plc.d/monitor-nagios
/usr/share/%{name}/nagios 
%{_sysconfdir}/cron.d/monitor-nagios.cron

%files server
%defattr(-,root,root)
#%config /usr/share/%{name}/monitorconfig.py
#%config /etc/monitor.conf
/var/lib/%{name}
/usr/share/%{name}/MANIFEST.in
/usr/share/%{name}/Makefile
/usr/share/%{name}/Monitor.spec
/usr/share/%{name}/README.txt
/usr/share/%{name}/RunlevelAgent.py*
/usr/share/%{name}/automate-default.sh
/usr/share/%{name}/monitor-default.conf
/usr/share/%{name}/monitor-runlevelagent.init
/usr/share/%{name}/monitor-server.cron
/usr/share/%{name}/monitor-server.init
/usr/share/%{name}/monitor.functions
/usr/share/%{name}/setup.py*
/usr/share/%{name}/threadpool.py*
/usr/share/%{name}/zabbix.spec

/usr/share/%{name}/bootcd
/usr/share/%{name}/commands
/usr/share/%{name}/config.d
/usr/share/%{name}/cron.d
/usr/share/%{name}/docs
/usr/share/%{name}/keys
/usr/share/%{name}/log
/usr/share/%{name}/statistics
/usr/share/%{name}/tests
/usr/share/%{name}/tools
/usr/share/%{name}/upgrade
/usr/share/%{name}/web
/usr/share/%{name}/zabbix

#/var/www/cgi-bin/monitor
%{_sysconfdir}/cron.d/monitor-server.cron
%{_sysconfdir}/plc.d/monitor
%{_sysconfdir}/plc.d/monitor.functions
%{_sysconfdir}/plc.d/zabbix
%{_sysconfdir}/httpd/conf.d
%{python_sitearch}


%files client
%defattr(-,root,root)
#%{_initrddir}/monitor
#%{_sysconfdir}/cron.d/monitor
/usr/bin/timeout.pl

%files runlevelagent
/usr/bin/RunlevelAgent.py*
/%{_initrddir}/monitor-runlevelagent


%post server-deps
#
# TODO: depend on distribution packages where feasible.
#
#  it would be better to be able to depend on the distribution's
# packages for these additional python modules, but packages provided
# by fedora 8 (our current deployment) doesn't match the version
# requirements.
export TMPDIR=/var/tmp/
#easy_install -UZ http://files.turbogears.org/eggs/TurboGears-1.0.7-py2.5.egg
#easy_install -UZ http://pypi.python.org/packages/source/S/SQLAlchemy/SQLAlchemy-0.5.3.tar.gz
#easy_install -UZ Elixir

# crazy openssl libs for racadm binary
ln -s /lib/libssl.so.0.9.8b /usr/lib/libssl.so.2
mkdir %{_datadir}/%{name}/.ssh
chmod 700 %{_datadir}/%{name}/.ssh

if grep 'pam_loginuid.so' /etc/pam.d/crond ; then
    sed -i -e 's/^session    required   pam_loginuid.so/#session    required   pam_loginuid.so/g' /etc/pam.d/crond
fi

# NOTE: enable monitor by default, since we're installing it.
if ! plc-config --category plc_monitor --variable enabled ; then 
	plc-config --category plc_monitor --variable enabled --value true \
			--save /etc/planetlab/configs/site.xml  /etc/planetlab/configs/site.xml 
fi
if ! plc-config --category plc_monitor --variable from_email ; then
	plc-config --category plc_monitor --variable from_email --value monitor@localhost.localdomain \
			--save /etc/planetlab/configs/site.xml /etc/planetlab/configs/site.xml 
fi
if ! plc-config --category plc_monitor --variable cc_email ; then
	plc-config --category plc_monitor --variable cc_email --value monitor@localhost.localdomain \
			--save /etc/planetlab/configs/site.xml /etc/planetlab/configs/site.xml 
fi
if ! plc-config --category plc_monitor --variable rt_queue ; then
	plc-config --category plc_monitor --variable rt_queue --value support \
			--save /etc/planetlab/configs/site.xml /etc/planetlab/configs/site.xml 
fi

%post nagios
# TODO: do as much as possible to get the host setup and running.
#chkconfig --add monitor-nagios
#chkconfig monitor-nagios on
chkconfig mysqld on

%post server
# TODO: this will be nice when we have a web-based service running., such as
# 		an API server or so on.
# TODO: create real monitorconfig.py from monitorconfig-default.py
# TODO: create symlink in /var/lib/monitor for chroot environments
# TODO: update the content of automate_pl03.sh 
# TODO: Use the installed version of bootcd to create custom boot images. ( or, use the api now).

# NOTE: generate the python defines from zabbix include files.
#php /usr/share/%{name}/zabbix/getdefines.php > %{python_sitearch}/monitor/database/zabbixapi/defines.py

# apply patches to zabbix
#patch -d /var/www/html/zabbix/ -p0 < /usr/share/%{name}/zabbix/zabbix-auto-login.diff

#chkconfig --add monitor-server
#chkconfig monitor-server on

%post client
chkconfig --add monitor
chkconfig monitor on

%post runlevelagent
if [ -f /etc/planetlab/node_id ] ; then
    chkconfig --add monitor-runlevelagent
    chkconfig monitor-runlevelagent on
    if [ "$PL_BOOTCD" != "1" ] ; then
        service monitor-runlevelagent restart
    fi
fi


%changelog
* Fri May 06 2011 s s <soltesz@cs.princeton.edu> - monitor-3.1-1
- last tag before some more major changes

* Thu May 20 2010 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-35
- Add CSV link on Advanced query
- Preparing to branch

* Wed May 12 2010 Talip Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-34
- * copy selections to clipbord on Advanced Query page
- * RPM Pattern as regexp
- * scan ipmi port

* Tue Apr 27 2010 Talip Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-33
- handle hostname changes

* Tue Apr 20 2010 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - Monitor-3.0-32
- from this version, suitable for 5.0
- requires bootcd with the new 5.0 naming style 3-part nodefamily

* Mon Apr 12 2010 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-31
- added fix for node delete/add causing conflicts in MyOps db.
- added statistics scripts

* Thu Jan 21 2010 Talip Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-30
- * fix paths for automate script

* Tue Dec 22 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-29
- - separate pcucontrol as an svn module
- - restore easy_instal back into post install stage of server-deps
- - template imporovements for web interface

* Thu Dec 17 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-28
- do not need buildrequires. a new tag to fix centos builds

* Thu Dec 17 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-27
- fix rpm build issues

* Wed Dec 16 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-26
- to many changes, but mostly moved stuff around. there are some small fixes here and there.

* Fri Nov 20 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-25
- add option for site status to include both node & pcu status
- improve ticket handling
- template gadget.xml for a site-specific google-gadget summary

* Thu Oct 22 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-24
- - add install_date

* Mon Oct 19 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-23
- - remove monitor-client.cron
- - remove unused monitor-client init script
- - fix UP/DOWN summary on nodes page.
- - make node page display all nodes by default
- - add boot_server field
- - add myops_ssh_key to the keychain
- - use ext_consortium_id to distinguish pending sites.

* Fri Oct 09 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-22
- show/hide advance query form.

* Thu Sep 24 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-21
- fixed pause_penalty bug.
- fixed IPAL pcucontrol bug
- fixed bootman tunnel setup bug (occurred in rare cases)
- deprecated pcuview
- added BootmanSequenceRecords to separate config data from source code
- added get/setBootmanSequence(s) to xmlrpc API

* Fri Sep 04 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-20
- Major Features:
- added bm log collection and optional integration with BootManager's log Upload()
- added iptables_status
- expanded advanced query
- added differentiated bootmanager_restore actions so that actionsummary displays
- counts for each kind of bootmanager action
- added pcuerror notices (for mis-configurations) in addition to pcufailed notices
- added plain-text options for query page by adding tg_format=plain to URL
- fixed cross-module reference that prevented pcucontrol for working with RebootNodeWithPCU() api call.
- fixed a bug in determining whether comon's dir was running on a node

* Mon Aug 17 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-19
- Major increment -
- adds multiple features and web changes
- adds new fields to db
- improved layout
- general improvements otherwise

* Sun Jun 28 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-18
- bug fixes.
- improved templates and views
- cleaned controller code for web
- added IPMI requirement to pcucontrol package.

* Thu Jun 18 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-17
- added bootmanager log links
- addressed root cause of IntegrityErrors ; big deal
- adjusted templates to accomodate fix for IntegrityErrors
- added session.flush() to bootman.py to write out ActionsRecords
- fixed policy to either pause penalties or apply them ; not both.

-* Wed Jun 17 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-16
-- Added Rpyc from 1.0 branch.
-- add pcuhistory
-- add setup-agent for password protected keys.
-- other minor improvements.

* Wed Jun 17 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-15
- automate install
- auto-close tickets

* Fri Jun 12 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-14
- update web
- update policy
- added statistics dir

* Mon Jun 08 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-13
- remove plccache from controllers, all lookups from db.
- reformat emailTxt messags
- updated bootstates in bootman.py

* Tue Jun 02 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-12
- tag of latest changes.
- need to test end to end.

* Sat May 30 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - Monitor-3.0-11
- big merge from the 2.0 branch

* Tue May 26 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - Monitor-3.0-10
- minor improvements in rendering with sortable tables

* Tue May 19 2009 Baris Metin <Talip-Baris.Metin@sophia.inria.fr> - Monitor-3.0-9

* Fri May 15 2009 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - Monitor-3.0-8
- first draft with sortable tables + checkpoint

* Fri May 15 2009 Baris Metin <tmetin@sophia.inria.fr>
- use plekit tables from plewww.
- depend on plewww-plekit

* Tue May 12 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-7
- make docs a noop
- fix for package name dependency
- correct docs

* Mon May 04 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-6
- add improved docs to the latest build and tag.

* Mon May 04 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-5
- add documentation hooks for adding in-line docs like NM and PLCAPI

* Fri May 01 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-4
- Rough pass over monitor-3.0 to allow it to work with 4.3 API.
- replaced GetNodeNetworks, nodeinterface_ids and using new bootstates
- 'safeboot', 'failboot', 'reinstall', etc.

* Tue Apr 28 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-3
- same as 2.0-12 tag.

* Mon Apr 27 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-2
- merge from 2.0, remove more zabbix code, simplify install, etc.

* Thu Apr 16 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-1
- major merge from 2.0 branch.
- ready to be updated with 4.3 and web changes.

* Fri Feb 27 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-1
- preparing to make a 2.0 branch for monitor.

* Mon Jan 05 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-0
- new changes are significantly different, that I'm upping the number for clarity.

* Wed Sep 24 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-8
- These are all changes in the latest Monitor code.  I will branch this version
- next, before making additional large changes.

* Mon Sep 01 2008 Thierry Parmentelat <thierry.parmentelat@sophia.inria.fr> - Monitor-1.0-7
- Checkpointing current version for 4.2-rc21 - many many changes

* Mon Aug 11 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-6
- This is a major tag of every thing.  probably needs a very different release
- number.

* Fri Jul 18 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-5
- Incremental improvements

* Mon May 19 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-4
- tagging everything for OneLab tech-transfer.
- 

* Fri May 09 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-3
- 

* Mon May 05 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-2
- 

* Wed Apr 23 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-1
- This should be ready for 4.2rc2
- 

* Mon Apr 07 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - monitor-1.0-0
- initial addition.

%define module_current_branch 3.0
