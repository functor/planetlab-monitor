#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/monitor/trunk/monitor.spec $

%define name monitor
%define version 1.0
%define taglevel 0

%define release %{taglevel}%{?date:.%{date}}

Summary: Monitor account initialization for the root image.
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

%description
Scripts for creating the monitor account in the root filesystem, to enable node access 
without using the 'root' account.

%prep
%setup -q

%build
echo "There is no build stage.  Simply copy files."

%install
rm -rf $RPM_BUILD_ROOT
install -D -m 755 monitor.init $RPM_BUILD_ROOT/%{_initrddir}/monitor
install -D -m 755 monitor.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/monitor

%clean
rm -rf $RPM_BUILD_ROOT

%files %{name}
%defattr(-,root,root)
%{_initrddir}/monitor
%{_sysconfdir}/cron.d/monitor

%post %{slicefamily}
chkconfig --add monitor
chkconfig monitor on

%changelog
* Mon Apr 07 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - monitor-1.0-0
- initial addition.
