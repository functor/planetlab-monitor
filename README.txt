Dependencies

  * RT - 3.4.1 - 
  	The version at rt.planet-lab.org is 3.4.1 and is incompatible with later
	versions of the command line tool.  

	The RPM pulls in *ALOT* of stuff; probably easier to work with from the
	source package, especially since all that's needed is the command line
	tool.  It has far fewer dependencies than the full RT package.

  * MySQL-python
  	python module necessary for connecting to the mysql RT database and
	extracting a list of open and new tickets.

  * util/PHPSerializer/PHPUnserializer
  	these are helper scripts for converting pickle objects into php serialize
	objects and back.

  * For iLO control over https, rather than SSH, you'll need the latest
    linux-LO* tools from HP. Searching for LOCFG.PL and Linux should get you
	a link.

		These required CPAN perl modules "Net::SSLeay" and "IO::Socket::SSL".
		These will pull in a bunch of other dependencies...

		$ perl -MCPAN -e "install Net::SSLeay"
		$ perl -MCPAN -e "install IO::Socket::SSL"

		I had to 'force install IO::Socket::SSL'...

		This mirror is reasonably fast: ftp://mirrors.ibiblio.org

  * For DRAC control over https rather than SSH
  		http://lanceerplaats.nl/PowerEdge/RAC/

  		$ perl -MCPAN -e "install Crypt::SSLeay"

  * For DRAC racadm:
  		Provides libstdc++-libc6.2-2.so.3:

  			rpm -ihv compat-libstdc++-7.3-2.96.110.i386.rpm
			rpm -ihv srvadmin-omilcore-4.5.0-335.i386.rpm
		    rpm -ihv srvadmin-racadm4-4.5.0-335.i386.rpm 

		The srvadmin rpms are available from the Dell Systems Management: Dell CD ISO

		Mounting it and copy out the 'srvadmin/linux' subdirectory.


		Have to suid root:
			chmod 4755 /usr/sbin/racadm
