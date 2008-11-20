#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/monitor/trunk/monitor.spec $

%define name monitor
%define version 1.1
%define taglevel 0

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

%package server
Summary: Monitor hooks for the PLC server.
Group: Applications/System

Requires: python
Requires: python-sqlalchemy
Requires: python-elixir

Requires: openssh-clients
Requires: perl-libwww-perl
Requires: perl-IO-Socket-SSL 
Requires: MySQL-python
Requires: rt3 == 3.4.1
Requires: nmap
Requires: PLCWWW >= 4.2
Requires: bootcd-planetlab-i386 >= 4.2

Requires: zabbix-client
Requires: zabbix-gui
Requires: zabbix-server

%description server
The server side include all python modules and scripts needed to fully
operation, track, and interact with any third-party monitoring software, such
as Zabbix DB.

%prep
%setup -q

%build
# NOTE: the build uses g++ cmdamt/
# NOTE: TMPDIR is needed here b/c the tmpfs of the build vserver is too small.
cd cmdamt
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

install -D -m 755 monitor-server.init $RPM_BUILD_ROOT/%{_sysconfdir}/plc.d/monitor

echo " * Installing core scripts"
rsync -a --exclude www --exclude archive-pdb --exclude .svn --exclude CVS \
	  ./ $RPM_BUILD_ROOT/usr/share/%{name}/

echo " * Installing web pages"
rsync -a www/ $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/

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
install -D -m 755 threadpool.py $RPM_BUILD_ROOT/%{python_sitearch}/threadpool.py

touch $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php
chmod 777 $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/monitorconfig.php

#install -D -m 755 monitor-default.conf $RPM_BUILD_ROOT/etc/monitor.conf
#cp $RPM_BUILD_ROOT/usr/share/%{name}/monitorconfig-default.py $RPM_BUILD_ROOT/usr/share/%{name}/monitorconfig.py

%clean
rm -rf $RPM_BUILD_ROOT

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

%files client
%defattr(-,root,root)
%{_initrddir}/monitor
%{_sysconfdir}/cron.d/monitor

%post server
# TODO: this will be nice when we have a web-based service running., such as
# 		an API server or so on.
# TODO: create real monitorconfig.py from monitorconfig-default.py
# TODO: create monitorconfig.php using phpconfig.py 
# TODO: create symlink in /var/lib/monitor for chroot environments
# TODO: update the content of automate_pl03.sh 
# TODO: Use the installed version of bootcd to create custom boot images. ( or, use the api now).

# NOTE: generate the python defines from zabbix include files.
php /usr/share/%{name}/zabbix/getdefines.php > %{python_sitearch}/monitor/database/zabbixapi/defines.py

#chkconfig --add monitor-server
#chkconfig monitor-server on

%post client
chkconfig --add monitor
chkconfig monitor on

%changelog
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

%define module_current_branch 1.0
