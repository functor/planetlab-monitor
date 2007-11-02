Dependencies

  * RT - 3.4.1 - 
  	The version at rt.planet-lab.org is 3.4.1 and is incompatible with later
	versions of the command line tool.  

	The RPM pulls in *ALOT* of stuff; probably easier to work with from the
	source package, especially, since all that's needed is the command line
	tool.  It has far fewer dependencies than the full RT package.

  * MySQL-python
  	python module necessary for connecting to the mysql RT database and
	extracting a list of open and new tickets.

  * util/PHPSerializer/PHPUnserializer
  	these are helper scripts for converting pickle objects into php serialize
	objects and back.
