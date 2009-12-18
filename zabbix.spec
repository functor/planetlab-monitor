%define debug_package %{nil}

%define _prefix		/usr/local/zabbix

Name:		zabbix
Version:	1.6.5
Release:	1
Group:		System Environment/Daemons
License:	GPL
Summary:	ZABBIX network monitor server
Vendor:		ZABBIX SIA
URL:		http://www.zabbix.org
Packager:	Eugene Grigorjev <eugene.grigorjev@zabbix.com>
Source:		zabbix-%{version}.tar.gz

Autoreq:	no
Buildroot: 	%{_tmppath}/%{name}-%{version}-%{release}-buildroot


#Prefix:		%{_prefix}

%define zabbix_bindir	%{_prefix}/bin
%define zabbix_datadir	%{_prefix}/misc
%define zabbix_confdir	%{_prefix}/conf
%define zabbix_initdir	%{_prefix}/init.d
%define zabbix_docdir	%{_prefix}/doc
%define zabbix_webdir	/var/www/html/zabbix
#%define zabbix_piddir	%{_tmppath}
#%define zabbix_logdir	%{_tmppath}

%define zabbix_piddir	/var/tmp
%define zabbix_logdir	/var/tmp

%description
The ZABBIX server is a network monitor

%package client
Summary:	ZABBIX network monitor agent daemon
Group:		System Environment/Daemons
%description client
The ZABBIX client is a network monitor

%package server
Summary:	ZABBIX network monitor server daemon
Group:		System Environment/Daemons
BuildPrereq: postgresql-devel
BuildPrereq: net-snmp-devel
#BuildPrereq: gnutls-devel
#BuildPrereq: libtasn1-devel

Requires: gnutls
Requires: postgresql-server
Requires: net-snmp

%description server
The ZABBIX server is a network monitor

%package gui
Summary:	ZABBIX network monitor server frontend
Group:		Productivity/Networking/Web/Frontends
Requires: php
Requires: php-bcmath
Requires: postgresql-server

%description gui
The ZABBIX gui frontend

%prep
%setup -n zabbix-%{version}

%build

# TODO: there must be a better way.  unfortunately, this package doesn't build
# after running ./configure from a subdir, i.e. mkdir client; cd client; ../configure... ; make-> fails.
mkdir client
cp -r * client || :
mkdir server
cp -r client/* server

pushd client
# quick and dirty fix for f12; loader would fail b/c of the lack of /lib/libm.a
%if "%{distro}" == "Fedora" && %{distrorelease} >= 12
./configure --enable-agent
%else
./configure --enable-static --enable-agent
%endif
make
popd

pushd server
./configure --enable-server --with-pgsql --with-net-snmp --with-libcurl
make
popd

%clean
rm -fr $RPM_BUILD_ROOT

%install
rm -fr $RPM_BUILD_ROOT

################# SERVER

# copy documentation
install -d %{buildroot}%{zabbix_docdir}
install -m 644 server/AUTHORS %{buildroot}%{zabbix_docdir}/AUTHORS
install -m 644 server/COPYING %{buildroot}%{zabbix_docdir}/COPYING
install -m 644 server/NEWS %{buildroot}%{zabbix_docdir}/NEWS
install -m 644 server/README %{buildroot}%{zabbix_docdir}/README

# copy binaries
install -d %{buildroot}%{zabbix_bindir}
install -s -m 755 server/src/zabbix_server/zabbix_server %{buildroot}%{zabbix_bindir}/zabbix_server

# copy config files
install -d %{buildroot}%{zabbix_confdir}
install -m 755 server/misc/conf/zabbix_server.conf %{buildroot}%{zabbix_confdir}/zabbix_server.conf
install -d %{buildroot}/etc/zabbix
install -m 755 server/misc/conf/zabbix_server.conf %{buildroot}/etc/zabbix

# copy startup script
install -d %{buildroot}%{zabbix_initdir}
install -m 755 server/misc/init.d/fedora/core/zabbix_server %{buildroot}%{zabbix_initdir}/zabbix_server

install -d %{buildroot}%{zabbix_datadir}
cp -r server/create %{buildroot}%{zabbix_datadir}

################# CLIENT 
# copy binaries
install -d %{buildroot}%{zabbix_bindir}
install -s -m 755 client/src/zabbix_agent/zabbix_agentd %{buildroot}%{zabbix_bindir}/zabbix_agentd

# copy config files
install -d %{buildroot}%{zabbix_confdir}
install -m 755 client/misc/conf/zabbix_agentd.conf %{buildroot}%{zabbix_confdir}/zabbix_agentd.conf
install -d %{buildroot}/etc/zabbix
install -m 755 client/misc/conf/zabbix_agentd.conf %{buildroot}/etc/zabbix

# copy startup script
install -d %{buildroot}%{zabbix_initdir}
install -m 755 client/misc/init.d/fedora/core/zabbix_agentd %{buildroot}%{zabbix_initdir}/zabbix_agentd

################# GUI
# copy php frontend
install -d %{buildroot}%{zabbix_webdir}
cp -r frontends/php/* %{buildroot}%{zabbix_webdir}

%post client
# create ZABBIX group
if [ -z "`grep zabbix /etc/group`" ]; then
  /usr/sbin/groupadd zabbix >/dev/null 2>&1
fi

# create ZABBIX uzer
if [ -z "`grep zabbix /etc/passwd`" ]; then
  /usr/sbin/useradd -g zabbix zabbix >/dev/null 2>&1
fi

# configure ZABBIX agentd daemon
TMP_FILE=`mktemp $TMPDIR/zbxtmpXXXXXX`

# TODO: setup Server=, Hostname=,
SERVER=`grep PLC_MONITOR_HOST /etc/planetlab/plc_config | tr "'" ' ' | awk '{print $2}'`
if [ -z "$SERVER" ] ; then
	SERVER=128.112.139.116
fi
HOST=`hostname`
sed	-e "s#Hostname=.*#Hostname=$HOST#g" \
	-e "s#Server=.*#Server=$SERVER#g" \
	-e "s#PidFile=/var/tmp/zabbix_agentd.pid#PidFile=%{zabbix_piddir}/zabbix_agentd.pid#g" \
	-e "s#LogFile=/tmp/zabbix_agentd.log#LogFile=%{zabbix_logdir}/zabbix_agentd.log#g" \
	%{zabbix_confdir}/zabbix_agentd.conf > $TMP_FILE
cat $TMP_FILE > %{zabbix_confdir}/zabbix_agentd.conf
mkdir -p /etc/zabbix
cp %{zabbix_confdir}/zabbix_agentd.conf /etc/zabbix/
# TODO: copy to /etc/zabbix/

sed	-e "s#BASEDIR=/opt/zabbix#BASEDIR=%{_prefix}#g" \
	-e "s#PIDFILE=/var/tmp/zabbix_agentd.pid#PIDFILE=%{zabbix_piddir}/zabbix_agentd.pid#g" \
	%{zabbix_initdir}/zabbix_agentd > $TMP_FILE
cat $TMP_FILE > %{zabbix_initdir}/zabbix_agentd

# NOTE: Run every runlevel as soon as possible, and stop as late as possible
cp %{zabbix_initdir}/zabbix_agentd %{_initrddir}
sed	-i -e "s#chkconfig: - 90 10#chkconfig: 2345 12 90#g" \
	%{_initrddir}/zabbix_agentd

rm -f $TMP_FILE

chkconfig --add zabbix_agentd 
chkconfig zabbix_agentd on
service zabbix_agentd start

%post server

# create ZABBIX group
if [ -z "`grep zabbix /etc/group`" ]; then
  /usr/sbin/groupadd zabbix >/dev/null 2>&1
fi

# create ZABBIX uzer
if [ -z "`grep zabbix /etc/passwd`" ]; then
  /usr/sbin/useradd -g zabbix zabbix >/dev/null 2>&1
fi

# configure ZABBIX server daemon
TMP_FILE=`mktemp $TMPDIR/zbxtmpXXXXXX`

sed	-e "s#AlertScriptsPath=/home/zabbix/bin/#AlertScriptsPath=%{zabbix_bindir}/#g" \
	-e "s#PidFile=/var/tmp/zabbix_server.pid#PidFile=%{zabbix_piddir}/zabbix_server.pid#g" \
	-e "s#LogFile=/tmp/zabbix_server.log#LogFile=%{zabbix_logdir}/zabbix_server.log#g" \
	-e "s|#DBPassword|DBPassword|g" \
	%{zabbix_confdir}/zabbix_server.conf > $TMP_FILE
cat $TMP_FILE > %{zabbix_confdir}/zabbix_server.conf
mkdir -p %{_sysconfdir}/zabbix
cp %{zabbix_confdir}/zabbix_server.conf %{_sysconfdir}/zabbix/

sed	-e "s#BASEDIR=/opt/zabbix#BASEDIR=%{_prefix}#g" \
	-e "s#PIDFILE=/var/tmp/zabbix_server.pid#PIDFILE=%{zabbix_piddir}/zabbix_server.pid#g" \
	%{zabbix_initdir}/zabbix_server > $TMP_FILE
cat $TMP_FILE > %{zabbix_initdir}/zabbix_server
rm -f $TMP_FILE

# NOTE: Run every runlevel as soon as possible, and stop as late as possible
cp %{zabbix_initdir}/zabbix_server %{_initrddir}
sed	-i -e "s#chkconfig: - 90 10#chkconfig: 2345 12 90#g" \
	%{_initrddir}/zabbix_server 

chkconfig --add zabbix_server
chkconfig zabbix_server on

%post gui
# Setup the necessary values in /etc/php.ini
# NOTE:  Zabbix requires max_execution_time to be 300 seconds
# NOTE:  Zabbix requires a default date.timezone 

# also edit  /var/www/html/zabbix/conf/zabbix.conf.php
#       touch  /var/www/html/zabbix/conf/zabbix.conf.php
#       chmod 644  /var/www/html/zabbix/conf/zabbix.conf.php
# 

TMP_FILE=`mktemp $TMPDIR/zbxtmpXXXXXX`
sed	-e "s#;date.timezone =#date.timezone = UTC#g" \
	-e "s#max_execution_time = 30 #max_execution_time = 300 #g" \
	%{_sysconfdir}/php.ini > $TMP_FILE
cat $TMP_FILE > %{_sysconfdir}/php.ini


%postun 
rm -f %{zabbix_piddir}/zabbix_server.pid
rm -f %{zabbix_logdir}/zabbix_server.log

rm -f %{zabbix_piddir}/zabbix_agentd.pid
rm -f %{zabbix_logdir}/zabbix_agentd.log

%files client
%defattr(-,root,root)

%dir %attr(0755,root,root) %{zabbix_confdir}
%attr(0644,root,root) %config(noreplace) %{zabbix_confdir}/zabbix_agentd.conf

%dir %attr(0755,root,root) %{zabbix_bindir}
%attr(0755,root,root) %{zabbix_bindir}/zabbix_agentd

%dir %attr(0755,root,root) %{zabbix_initdir}
%attr(0755,root,root) %{zabbix_initdir}/zabbix_agentd

%config /etc/zabbix/zabbix_agentd.conf

%files server
%defattr(-,root,root)

%dir %attr(0755,root,root) %{zabbix_docdir}
%attr(0644,root,root) %{zabbix_docdir}/AUTHORS
%attr(0644,root,root) %{zabbix_docdir}/COPYING
%attr(0644,root,root) %{zabbix_docdir}/NEWS
%attr(0644,root,root) %{zabbix_docdir}/README

%dir %attr(0755,root,root) %{zabbix_confdir}
%attr(0644,root,root) %config(noreplace) %{zabbix_confdir}/zabbix_server.conf

%dir %attr(0755,root,root) %{zabbix_bindir}
%attr(0755,root,root) %{zabbix_bindir}/zabbix_server

%dir %attr(0755,root,root) %{zabbix_initdir}
%attr(0755,root,root) %{zabbix_initdir}/zabbix_server

%dir %attr(0755,root,root) %{zabbix_datadir}
%attr(0755,root,root) %{zabbix_datadir}/create/

%config /etc/zabbix/zabbix_server.conf

%files gui
%defattr(-,root,root)
%dir %{zabbix_webdir}
%{zabbix_webdir}

%changelog
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

* Wed Jun 17 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-3.0-16
- Added Rpyc from 1.0 branch.
- add pcuhistory
- add setup-agent for password protected keys.
- other minor improvements.

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

* Fri Apr 03 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-9
- added new models to db.
- major updates throughout.
- better unification. needs an install test.

* Wed Apr 01 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-8
- removed old pkl database references.
- added blacklist to db model
- added fix to IntelAMT remoteControl to start an power-down node
- added policy.py
- added global error count before bailing entirely.

* Fri Mar 27 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-7
- improved db model
- updated files that use db model
- updated web view based on node, site, and pcu states.
- added local mirror to zabbix Make file.

* Tue Mar 24 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-6
- added action view to gui
- added penalty_applied bit to db model.

* Fri Mar 20 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-5
- tag for updates to 2.0 db model

* Fri Mar 13 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-4
- splits reboot.py across pcucontrol and monitor modules
- moves command.py from monitor/util to pcucontrol/util

* Tue Mar 10 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-3
- add email exceptions
- other bug fixes.

* Tue Mar 10 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-2
- getting the pcucontrol and findall.py scripts to work in an integrated
- fashion.

* Fri Feb 27 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-1
- preparing to make a 2.0 branch for monitor.

* Mon Jan 05 2009 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-2.0-0
- new changes are significantly different, that I'm upping the number for clarity.

* Tue Nov 11 2008 Stephen Soltesz <soltesz@cs.princeton.edu>
- 1.6.1
- initial re-packaging

* Thu Dec 01 2005 Eugene Grigorjev <eugene.grigorjev@zabbix.com>
- 1.1beta2
- initial packaging


%define module_current_branch 2.0

%define taglevel 28

%define version 3.0
