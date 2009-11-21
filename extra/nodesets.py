#!/usr/bin/python

import sys
import os
from sets import Set
from monitor import parser as parsermodule
from monitor.util import file

def main():
	parser = parsermodule.getParser()
	parser.set_defaults(operation="and",)
	parser.add_option("", "--operation", dest="operation", metavar="and", 
						help="""Which operation to perform on the two sets.  (and, or, minus""")

	config = parsermodule.parse_args(parser)

	f1 = config.args[0]
	f2 = config.args[1]

	s1 = file.getListFromFile(f1)
	s2 = file.getListFromFile(f2)

	s = nodesets(config.operation, s1, s2)

	if config.operation == "and":
		print "Nodes in both sets", len(Set(s1) & Set(s2))
	elif config.operation == "uniquetoone" or config.operation == "minus":
		print "Nodes unique to set 1", len(Set(s1) - Set(s2))
	elif operation == "or":
		print "Union of nodes in both sets", len(Set(s1) | Set(s2))

	for i in s:
		print i


def nodesets(operation, s1, s2):

	if operation == "and":
		return Set(s1) & Set(s2)
	elif operation == "uniquetoone" or operation == "minus":
		return Set(s1) - Set(s2)
	elif operation == "or":
		return Set(s1) | Set(s2)
	else:
		print "Unknown operation: %s " % operation
	
	return []

if __name__ == "__main__":
	main()
