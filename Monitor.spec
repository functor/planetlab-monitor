#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/monitor/trunk/monitor.spec $

%define name monitor
%define version 1.0
%define taglevel 2

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

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

Requires: curl
Requires: coreutils

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

%files
%defattr(-,root,root)
%{_initrddir}/monitor
%{_sysconfdir}/cron.d/monitor

%post
chkconfig --add monitor
chkconfig monitor on

%changelog
* Mon May 05 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-2
- 

* Wed Apr 23 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-1.0-1
- This should be ready for 4.2rc2
- 

* Mon Apr 07 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - monitor-1.0-0
- initial addition.
