#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/monitor/trunk/monitor.spec $

%define name monitor
%define version 3.0
%define taglevel 17

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
Requires: TurboGears

Requires: compat-libstdc++-296
Requires: openssh-clients
Requires: perl-libwww-perl
Requires: perl-IO-Socket-SSL 
Requires: MySQL-python
Requires: nmap
Requires: rt3

Requires: plewww-plekit

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
Requires: monitor-pcucontrol
Requires: PLCWWW >= 4.2
Requires: bootcd-%{pldistro}-%{_arch} >= 4.2

%description server
The server side include all python modules and scripts needed to fully
operation, track, and interact with any third-party monitoring software, such
as Zabbix DB.

######################################## RT setup

%package rt
summary: Dependencies and default configuration for RT3
group: applications/system
Requires: monitor-server
Requires: rt3
Requires: rt3-mailgate

%description rt
RT3 is a ticket tracking system.  This RPM integrates RT into the MyOps
framework, and MyPLC in general.

######################################## PCU Control

%package pcucontrol
summary: pcu controls for monitor and plcapi
group: applications/system
requires: python
requires: OpenIPMI-tools

%description pcucontrol
both monitor and the plcapi use a set of common commands to reboot machines
using their external or internal pcus.  this package is a library of several
supported models.

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

%build
# NOTE: the build uses g++ cmdamt/
# NOTE: TMPDIR is needed here b/c the tmpfs of the build vserver is too small.
cd pcucontrol/models/intelamt
export TMPDIR=$PWD/tmp
make
cd ..

%install
rm -rf $RPM_BUILD_ROOT
#################### CLIENT 
install -D -m 755 monitor-client.init $RPM_BUILD_ROOT/%{_initrddir}/monitor
install -D -m 644 monitor.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor

#################### SERVER
install -d $RPM_BUILD_ROOT/usr/share/%{name}
install -d $RPM_BUILD_ROOT/data/var/lib/%{name}
install -d $RPM_BUILD_ROOT/data/var/lib/%{name}/archive-pdb
install -d $RPM_BUILD_ROOT/var/lib/%{name}
install -d $RPM_BUILD_ROOT/var/lib/%{name}/archive-pdb
install -d $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/
install -d $RPM_BUILD_ROOT/var/www/html/monitorlog/

install -D -m 644 monitor.functions $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor.functions
install -D -m 755 monitor-server.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor
install -D -m 755 zabbix/monitor-zabbix.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/zabbix
install -D -m 755 rt3/monitor-rt3.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/rt3

echo " * Installing core scripts"
rsync -a --exclude www --exclude archive-pdb --exclude .svn --exclude CVS \
	  ./ $RPM_BUILD_ROOT/usr/share/%{name}/

echo " * Installing web pages"
rsync -a www/ $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/
rsync -a log/ $RPM_BUILD_ROOT/var/www/html/monitorlog/

echo " * Installing cron job for automated polling"
install -D -m 644 monitor-server.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor-server.cron
echo " * TODO: Setting up Monitor account in local MyPLC"
# TODO: 

install -d $RPM_BUILD_ROOT/%{python_sitearch}/monitor
install -d -D -m 755 monitor $RPM_BUILD_ROOT/%{python_sitearch}/monitor
# TODO: need a much better way to do this.
rsync -a monitor/ $RPM_BUILD_ROOT/%{python_sitearch}/monitor/
#for file in __init__.py database.py config.py ; do 
#	install -D -m 644 monitor/$file $RPM_BUILD_ROOT/%{python_sitearch}/monitor/$file
#done
rsync -a pcucontrol/ $RPM_BUILD_ROOT/%{python_sitearch}/pcucontrol/
install -D -m 755 threadpool.py $RPM_BUILD_ROOT/%{python_sitearch}/threadpool.py

touch $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php
chmod 777 $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php

install -D -m 644 rt3/rt.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/rt.cron
chmod 755 $RPM_BUILD_ROOT/usr/share/%{name}/rt3/adduserstort.pl
chmod 755 $RPM_BUILD_ROOT/usr/share/%{name}/rt3/rtcron.d/*.sh
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

%files server
%defattr(-,root,root)
#%config /usr/share/%{name}/monitorconfig.py
#%config /etc/monitor.conf
/usr/share/%{name}
/var/lib/%{name}
/var/www/cgi-bin/monitor
%{_sysconfdir}/cron.d/monitor-server.cron
%{python_sitearch}/threadpool.py
%{python_sitearch}/threadpool.pyc
%{python_sitearch}/threadpool.pyo
%{python_sitearch}/monitor
%{_sysconfdir}/plc.d/monitor
%{_sysconfdir}/plc.d/monitor.functions
%{_sysconfdir}/plc.d/zabbix

%files client
%defattr(-,root,root)
%{_initrddir}/monitor
%{_sysconfdir}/cron.d/monitor

%files rt 
%defattr(-,root,root)
/usr/share/%{name}/rt3
%{_sysconfdir}/plc.d/rt3
%{_sysconfdir}/cron.d/rt.cron

%files pcucontrol
%{python_sitearch}/pcucontrol

%files runlevelagent
/usr/bin/RunlevelAgent.py
/usr/bin/RunlevelAgent.pyo
/usr/bin/RunlevelAgent.pyc
/%{_initrddir}/monitor-runlevelagent

%post server-deps
#easy_install --build-directory /var/tmp -UZ ElementTree
##easy_install --build-directory /var/tmp -UZ http://pypi.python.org/packages/2.5/E/Extremes/Extremes-1.1-py2.5.egg


## TODO: something is bad wrong with this approach.
easy_install --build-directory /var/tmp -UZ http://files.turbogears.org/eggs/TurboGears-1.0.7-py2.5.egg
easy_install --build-directory /var/tmp -UZ http://pypi.python.org/packages/source/S/SQLAlchemy/SQLAlchemy-0.5.3.tar.gz
easy_install --build-directory /var/tmp -UZ Elixir

# crazy openssl libs for racadm binary
ln -s /lib/libssl.so.0.9.8b /usr/lib/libssl.so.2
mkdir /usr/share/monitor/.ssh
chmod 700 /usr/share/monitor/.ssh

if grep 'pam_loginuid.so' /etc/pam.d/crond ; then
    sed -i -e 's/^session    required   pam_loginuid.so/#session    required   pam_loginuid.so/g' /etc/pam.d/crond
fi
# NOTE: add the default xml stuff if it's not already in the default xml config.
if ! grep '<category id="plc_monitor">' /etc/planetlab/default_config.xml ; then 
    sed -i 's|<category id="plc_net">| <category id="plc_monitor">\n <name>Monitor Service Configuration</name>\n <description>Monitor</description>\n <variablelist>\n <variable id="enabled" type="boolean">\n <name>Enabled</name>\n <value>true</value>\n <description>Enable on this machine.</description>\n </variable>\n <variable id="email">\n <value></value>\n </variable>\n <variable id="dbpassword">\n <value></value>\n </variable>\n <variable id="host" type="hostname">\n <name>Hostname</name>\n <value>pl-virtual-06.cs.princeton.edu</value>\n <description>The fully qualified hostname.</description>\n </variable>\n <variable id="ip" type="ip">\n <name>IP Address</name>\n <value/>\n <description>The IP address of the monitor server.</description>\n </variable>\n </variablelist>\n </category>\n <category id="plc_net">|' /etc/planetlab/default_config.xml
fi
if ! grep '<category id="plc_rt">' /etc/planetlab/default_config.xml ; then 
    sed -i 's|<category id="plc_net">| <category id="plc_rt">\n <name>RT Configuration</name>\n <description>RT</description>\n <variablelist>\n <variable id="enabled" type="boolean">\n <name>Enabled</name>\n <value>false</value>\n <description>Enable on this machine.</description>\n </variable>\n <variable id="host" type="hostname">\n <name>Hostname</name>\n <value>localhost.localdomain</value>\n <description>The fully qualified hostname.</description>\n </variable>\n <variable id="ip" type="ip">\n <name>IP Address</name>\n <value/>\n <description>The IP address of the RT server.</description>\n </variable>\n </variablelist>\n </category>\n <category id="plc_net">|' /etc/planetlab/default_config.xml
fi
if ! grep '<category id="plc_zabbix">' /etc/planetlab/default_config.xml ; then 
    sed -i 's|<category id="plc_net">| <category id="plc_zabbix">\n <name>Zabbix Configuration</name>\n <description>Zabbix</description>\n <variablelist>\n <variable id="enabled" type="boolean">\n <name>Enabled</name>\n <value>false</value>\n <description>Enable on this machine.</description>\n </variable>\n <variable id="host" type="hostname">\n <name>Hostname</name>\n <value>localhost.localdomain</value>\n <description>The fully qualified hostname.</description>\n </variable>\n <variable id="ip" type="ip">\n <name>IP Address</name>\n <value/>\n <description>The IP address of the Zabbix server.</description>\n </variable>\n </variablelist>\n </category>\n <category id="plc_net">|' /etc/planetlab/default_config.xml
fi

# NOTE: enable monitor by default, since we're installing it.
plc-config --save /etc/planetlab/default_config.xml \
			--category plc_monitor --variable enabled --value true

%post rt
plc-config --save /etc/planetlab/default_config.xml \
			--category plc_rt --variable enabled --value true

%post server
# TODO: this will be nice when we have a web-based service running., such as
# 		an API server or so on.
# TODO: create real monitorconfig.py from monitorconfig-default.py
# TODO: create monitorconfig.php using phpconfig.py 
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
chkconfig --add monitor-runlevelagent
chkconfig monitor-runlevelagent on
if [ "$PL_BOOTCD" != "1" ] ; then
	service monitor-runlevelagent restart
fi


%changelog
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

%define module_current_branch 2.0
