#!/usr/bin/python

import pprint
import sys
import soltesz

pp = pprint.PrettyPrinter(indent=4) 
o = soltesz.dbLoad(sys.argv[1])
pp.pprint(o) 
