# A simple authentication file for access to plc:
# NOTE: only hosts can be checked anonymously, users cannot be.

#auth = {'Username' : '', 'AuthMethod' : 'password', 'AuthString' : ''}
auth = {'AuthMethod' : "anonymous"}
plc = "https://boot.planet-lab.org/PLCAPI/"

