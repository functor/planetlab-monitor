#!/usr/bin/python

from config import config as cfg
import sys
import os
from sets import Set
from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.set_defaults(operation="and",)
	parser.add_option("", "--operation", dest="operation", metavar="and", 
						help="""Which operation to perform on the two sets.  (and, or, minus""")

	config = cfg(parser)
	config.parse_args()

	f1 = config.args[0]
	f2 = config.args[1]

	s1 = config.getListFromFile(f1)
	s2 = config.getListFromFile(f2)

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
