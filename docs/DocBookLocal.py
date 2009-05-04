#!/usr/bin/env python

# PATHS to be set by the build system
# this is in ..
from monitor_xmlrpc import MonitorXmlrpcServer as docobject
# in PLCAPI/doc
from DocBook import DocBook

def api_methods():
    api_function_list = []
    for func in dir(docobject):
        try:
            f = getattr(docobject,func)
            if 'group' in f.__dict__.keys():
                    api_function_list += [getattr(docobject,func)]
        except:
            pass
    return api_function_list

DocBook(api_methods ()).Process()
