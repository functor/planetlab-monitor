#!/usr/bin/python

import pprint
import sys
import database

pp = pprint.PrettyPrinter(indent=4) 
o = database.dbLoad(sys.argv[1])
pp.pprint(o) 
