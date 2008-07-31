#
# $Id$
# 

%define url $URL: svn+ssh://svn.planet-lab.org/svn/Monitor/trunk/Monitor-server.spec $

%define name monitor-server
%define version 1.0
%define taglevel 5

%define release %{taglevel}%{?pldistro:.%{pldistro}}%{?date:.%{date}}

Summary: Monitor backend scripts for server
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
Requires: PLCWWW >= 4.2

%description
Scripts for polling PLC, the node, and PCU status.  Also a collection of
command-line utilities for querying the status database. 

%prep
%setup -q

%build
echo "There is no build stage.  Simply copy files."

%install

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/share/%{name}
mkdir -p $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/

echo " * Installing core scripts"
rsync -a --exclude www --exclude archive-pdb --exclude .svn --exclude CVS \
	  ./ $RPM_BUILD_ROOT/usr/share/%{name}/

echo " * Installing web pages"
rsync -a www/ $RPM_BUILD_ROOT/var/www/cgi-bin/monitor/

echo " * TODO: Installing cron job for automated polling"
install -D -m 755 %{name}.cron $RPM_BUILD_ROOT/%{_sysconfdir}/cron.d/%{name}
echo " * TODO: Setting up Monitor account in local MyPLC"

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
# define a %config entry for /var/share/%{name}/xyz?
/usr/share/%{name}
/var/www/cgi-bin/monitor
%{_sysconfdir}/cron.d/%{name}

%post
echo "Post processing"
# TODO: this will be nice when we have a web-based service running., such as
# 		an API server or so on.
#chkconfig --add monitor-server
#chkconfig monitor-server on

%changelog
* Wed Jul 30 2008 Stephen Soltesz <soltesz@cs.princeton.edu> - Monitor-server-1.0-5
- initial creation of server-side package